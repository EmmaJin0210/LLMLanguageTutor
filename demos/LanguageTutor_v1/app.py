from fastapi import FastAPI, Form, File, Request, status, WebSocket, WebSocketDisconnect, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from core.utils.profile_utils import *
from core.utils.speech_utils import *
from core.utils.utils import *
from core.learning_mode import *
from core.conversation_mode import *
import shutil

app = FastAPI()

app.mount("/core/temp-data", StaticFiles(directory="core/temp-data"), name="temp-data")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

all_users_db_path = "user_profiles/all_users.json"
all_users = read_json_to_dict(all_users_db_path)
levels = []

session_data = {}

@app.get("/")
def get_root(request: Request):
    if "username" in session_data:
        return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/home", response_class=HTMLResponse)
async def get_home(request: Request):
    if "username" in session_data:
        language = session_data["language"] if "language" in session_data else None
        return templates.TemplateResponse("home.html", {"request": request, "selected": language})
    else:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/signup")
async def get_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
def sign_up(request: Request, username: str = Form(...), first_name: str = Form(...)):
    username = username.lower()
    all_users[username] = {"username": username, "firstname": first_name}
    write_dict_to_json(all_users, "user_profiles/all_users.json")
    user_template = read_json_to_dict("user_profiles/<username>.json")
    user_template["name"] = first_name
    write_dict_to_json(user_template, f"user_profiles/{username}.json")
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/login")
async def get_login(request: Request):
    if "username" in session_data:
        return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request, username: str = Form(...)):
    global session_data
    if username in all_users:
        print("storing session stuff")
        session_data['username'] = username
        session_data['profile_path'] = retrieve_profile_path_from_username(username)
        profile = read_json_to_dict(f"user_profiles/{username}.json")
        session_data['profile'] = profile
        session_data["firstname"] = profile["name"]
        return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return HTMLResponse(content="<p>Invalid username. Try again or <a href='/signup'>sign up</a>.</p>", status_code=400)
    

@app.get("/logout")
def logout(request: Request):
    global session_data
    session_data = {}
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/set-language")
def set_language(request: Request, language: str = Form(...)):
    global levels, session_data
    if "username" in session_data:
        print("language: ", language)
        session_data['language'] = language
        levels = get_levels(language)
        return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/choose-instruction-lang")
async def get_instruction_lang(request: Request):
    if "username" in session_data:
        return templates.TemplateResponse("instruction-lang.html", {"request": request, "levels": levels})
    else:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/set-instruction-lang")
def set_instruction_lang(request: Request, instructionlang: str = Form(...), targetlevel: str = Form(...)):
    global session_data
    session_data['instruction_language'] = instructionlang
    session_data['target_level'] = targetlevel
    return RedirectResponse(url="/learning", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/choose-backup-lang")
async def get_backup_lang(request: Request):
    if "username" in session_data:
        return templates.TemplateResponse("backup-lang.html", {"request": request, "levels": levels})
    else:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/set-backup-lang")
def set_backup_lang(request: Request, backuplang: str = Form(...), currentlevel: str = Form(...)):
    global session_data
    session_data['backup_language'] = backuplang
    session_data['current_level'] = currentlevel
    return RedirectResponse(url="/conversation", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/learning")
async def get_learning_mode(request: Request):
    if "username" in session_data:
        return templates.TemplateResponse("learning.html", {"request": request, "language": session_data["language"]})
    else:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/save-learning")
def save_learning_mode(request: Request):
    global session_data
    try:
        grammar_to_teach = session_data["grammar_to_teach"]
        user_profile = session_data["profile"]
        user_profile = update_learning_log_in_profile(grammar_to_teach, user_profile)
        profile_path = session_data["profile_path"]
        write_updated_profile_to_file(user_profile, profile_path)
        return JSONResponse(status_code=200, content={"message": "Progress saved! Your learning and conversation sessions hereon will take into account what you learned today.\n\nRedirecting to homepage..."})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"message": "Failed to save progress"})


@app.websocket("/ws-learning")
async def websocket_endpoint_learning(websocket: WebSocket):
    global session_data
    await websocket.accept()

    learning_schema = "random-sample"
    name = session_data["firstname"]
    if session_data["profile"]["comprehension-level"]:
        level = session_data["profile"]["comprehension-level"]
    else:
        level = get_desc(session_data["target_level"])
    target_language = session_data["language"]
    instruction_language = session_data["instruction_language"]
    grammar_dict_target = load_grammar_file_to_dict(target_language, [session_data["target_level"]])
    user_profile = session_data["profile"]
    grammar_to_teach = pick_grammars_to_teach(learning_schema, grammar_dict_target, user_profile)
    session_data["grammar_to_teach"] = grammar_to_teach
    sys_prompt = construct_learning_sys_prompt(name, level, target_language, instruction_language, grammar_to_teach)
    my_key = os.getenv("OPENAI_API_KEY")
    engine = OpenAIEngine(my_key, model="gpt-4")
    session_data["engine"] = engine
    tutor = LearningKani(user_profile=user_profile, engine=engine, system_prompt=sys_prompt)
    try:
        while True:
            data = await websocket.receive()
            if "text" in data:
                try:
                    data = json.loads(data["text"])
                    datatype = data["type"]
                    datadata = data["data"]
                except:
                    datatype = "text"
                    datadata = data["text"]

                if datatype == "text":
                    user_input = datadata
                elif datatype == "audio":
                    file_location = "core/temp-data/input.wav"
                    transcription = await transcribe_audio(file_location)
                    print("transcription ", transcription)
                    user_input = transcription["transcription"]
                    await websocket.send_text(f"You:{user_input}")
                
                async for msg in tutor.full_round(user_input):
                    if msg.content is None and msg.role == ChatRole.ASSISTANT:
                        continue
                    if msg.role == ChatRole.FUNCTION:
                        continue
                    await websocket.send_text("Tutor:" + msg.text)
                    audio_url = await generate_audio_response(msg.text)
                    await websocket.send_text(audio_url)
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        await clean_up(engine)


@app.get("/conversation")
async def get_conversation_mode(request: Request):
    if "username" in session_data:
        return templates.TemplateResponse("conversation.html", {"request": request})
    else:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/save-conversation")
async def save_conversation_mode(request: Request):
    global session_data
    try:
        language = session_data["language"]
        user_profile = session_data["profile"]
        profile_path = session_data["profile_path"]
        tutor = session_data["tutor"]
        engine = session_data["engine"]
        if user_interests:
            user_profile["interests"] = summarize_user_interests(user_interests, language)
        if user_info:
            user_profile["personal-info"] = summarize_user_personal_info(user_info, language)
        # summarize topics talked about
        history_to_summarize = format_chat_history_for_summary(tutor.chat_history)
        topics_talked_about = summarize_rounds_history(history_to_summarize, language)
        user_profile["past-topics"].append(topics_talked_about)
        write_updated_profile_to_file(user_profile, profile_path)
        return JSONResponse(status_code=200, content={"message": "Progress saved! Your learning and conversation sessions hereon will take into account what you learned today.\n\nRedirecting to homepage..."})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"message": "Failed to save progress"})
    finally:
        await clean_up(engine)
    


@app.websocket("/ws-conversation")
async def websocket_endpoint_conversation(websocket: WebSocket):
    global session_data, user_interests, user_info
    await websocket.accept()

    mode = "formal"
    track_usage = False
    level = get_desc(session_data["current_level"])
    language = session_data["language"]
    target_level = session_data["current_level"]
    backup_lanaguage = session_data["backup_language"]
    levels_below = get_levels_below_inclusive(language, target_level)
    levels_above = get_levels_above_exclusive(language, target_level)

    grammar_dict_target = load_grammar_file_to_dict(language, levels_below)
    grammar_points_target = get_grammar_keys(grammar_dict_target)

    grammar_dict_above = load_grammar_file_to_dict(language, levels_above)
    grammar_points_above = get_grammar_keys(grammar_dict_above)
    gd_above = GrammarDetectorLevel(language, grammar_points_above)

    tokenizer = SentenceTokenizer(language)

    vocab_dict_target =  load_vocab_file_to_dict(language, levels_below)
    vocab_points_target = get_vocab_keys_w_category(vocab_dict_target)
    vocab_keys_target = get_vocab_keys(vocab_points_target)

    vocab_dict_above =  load_vocab_file_to_dict(language, levels_above)
    vocab_points_above = get_vocab_keys_w_category(vocab_dict_above)
    vocab_keys_above = get_vocab_keys(vocab_points_above)
    vd_above = VocabDetector(language, vocab_points_above, vocab_keys_above)

    ss = SentenceSimplifier(language, backup_lanaguage, grammar_points_target, grammar_points_above, vocab_keys_target, vocab_keys_above)

    user_profile = session_data["profile"]
    name = session_data["firstname"]
    user_interests = retrieve_user_interests_from_profile(user_profile)
    user_info = retrieve_user_info_from_profile(user_profile)
    past_topics = retrieve_past_topics_from_profile(user_profile)
    good_grammar = retrieve_recent_grammar_learnt(user_profile)
    system_prompt = construct_sys_prompt_conversation(language, backup_lanaguage, name, level, user_interests, user_info, past_topics, good_grammar)

    my_key = os.getenv("OPENAI_API_KEY")
    engine = OpenAIEngine(my_key, model="gpt-4")
    session_data["engine"] = engine
    tutor = ConversationKani(user_profile=user_profile, engine=engine, system_prompt=system_prompt, desired_response_tokens=15)
    session_data["tutor"] = tutor
    try:
        rounds = 0
        all_user_input = ""
        all_bot_output = ""
        user_interests = [user_profile["interests"]]
        user_info = [user_profile["personal-info"]]
        while True:
            if rounds % 16 == 0 and rounds != 0:
                history_to_summarize = format_chat_history_for_summary(
                    tutor.chat_history[:len(tutor.chat_history-4)])
                chat_summary = summarize_rounds_history(history_to_summarize, language)
                new_chat_history = [ChatMessage(role=ChatRole.ASSISTANT, content=chat_summary)] +\
                                    tutor.chat_history[len(tutor.chat_history-4):]
                tutor.chat_history = new_chat_history
            data = await websocket.receive()
            try:
                data = json.loads(data["text"])
                datatype = data["type"]
                datadata = data["data"]
            except:
                datatype = "text"
                datadata = data["text"]

            if datatype == "text":
                user_input = datadata
            elif datatype == "audio":
                file_location = "core/temp-data/input.wav"
                transcription = await transcribe_audio(file_location)
                print("transcription ", transcription)
                user_input = transcription["transcription"]
                await websocket.send_text(f"You:{user_input}")
            
            async for msg in tutor.full_round(user_input):
                if msg.content is None and msg.role == ChatRole.ASSISTANT:
                    continue
                if msg.role == ChatRole.FUNCTION:
                    if msg.name == "store_user_interest":
                        user_interests.append(msg.content)
                    elif msg.name == "store_user_personal_info":
                        user_info.append(msg.content)
                    continue
                print("orgininal text: ", msg.text)
                tokens = tokenizer.tokenize_sentence(msg.text)
                gp_above = await gd_above.detect_grammar(msg.text)
                for gp in gp_above:
                    if gp in grammar_points_target or gp not in gd_above.grammar_points:
                        gp_above.remove(gp)
                print("above grammar: ", gp_above)
                vp_above = vd_above.detect_vocab(tokens)
                for i, vp in enumerate(vp_above):
                    if vp in all_user_input:
                        vp_above.pop(i)
                print("above vocab: ", vp_above)
                if len(gp_above) != 0 or len(vp_above) != 0:
                    print("Simplifying...")
                    if mode == "formal":
                        text = ss.swap_hard_expressions_formal(gp_above + vp_above, msg.text)
                    else:
                        text = ss.swap_hard_expressions_casual(gp_above + vp_above, msg.text)
                else:
                    text = msg.text
                tutor.chat_history[-1] = ChatMessage.assistant(text)
                await websocket.send_text("Tutor:" + text)
                audio_url = await generate_audio_response(text)
                await websocket.send_text(audio_url)
            rounds += 1
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        await clean_up(engine)


async def generate_audio_response(text):
    audio_filename = text_to_speech_web(text)
    server_address = os.getenv("SERVER_ADDRESS", "127.0.0.1:8000")
    return f"http://{server_address}/core/temp-data/{audio_filename}"


async def transcribe_audio(file_path: str):
    try:
        client = OpenAI()
        with open(file_path, "rb") as audiofile:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audiofile
            )
            print("Transcription: ", transcription.text)
            return {"transcription": transcription.text}
    except Exception as e:
        print(f"Error in transcription: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to transcribe audio."})


@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    file_location = f"core/temp-data/{file.filename}"
    print("file loc: ", file_location)
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return JSONResponse(content={"status": "success"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)