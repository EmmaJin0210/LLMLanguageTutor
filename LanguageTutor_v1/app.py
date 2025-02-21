from fastapi import FastAPI, Form, File, Request, Response, status, UploadFile, \
    WebSocket, WebSocketDisconnect, \
    HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import shutil

from core.kanis.ConversationKani import ConversationKani
from core.kanis.LearningKani import LearningKani
from core.core_utils.language_utils import get_all_levels
from core.core_utils.chat_utils import summarize_chat_history
from core.core_utils.engine_utils import clean_up

from appstuff.data_classes import GlobalSessionData
from appstuff.app_utils.app_utils import *

from core.core_constants import CHAT_ENGINE, CHAT_MODEL, LEARNING_ENGINE, LEARNING_MODEL
from appstuff.app_constants import FILENAME_USERS_DB, \
    ROOT_TEMP_DATA, ROOT_STATIC, ROOT_TEMPLATES, \
    MOUNT_TEMP_DATA, MOUNT_STATIC, \
    APP_IP, APP_PORT


app = FastAPI()

app.mount(MOUNT_TEMP_DATA, StaticFiles(directory = ROOT_TEMP_DATA), name = "temp-data")
app.mount(MOUNT_STATIC, StaticFiles(directory = ROOT_STATIC), name = "static")
templates = Jinja2Templates(directory = ROOT_TEMPLATES)

g_session_data = GlobalSessionData()
g_session_data.users = read_json_to_dict(f"{ROOT_USER_PROFILES}{FILENAME_USERS_DB}")

@app.get("/")
def get_root(request: Request) -> RedirectResponse:
    if g_session_data.username:
        return RedirectResponse(url = "/home", status_code = status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url = "/login", status_code = status.HTTP_303_SEE_OTHER)


@app.get("/home", response_class=HTMLResponse)
async def get_home(request: Request) -> Response:
    if g_session_data.username:
        language = g_session_data.language
        return templates.TemplateResponse("home.html", {"request": request, "selected": language})
    else:
        return RedirectResponse(url = "/login", status_code = status.HTTP_303_SEE_OTHER)


@app.get("/signup")
async def get_signup(request: Request) -> Response:
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
def sign_up(request: Request, username: str = Form(...), first_name: str = Form(...)) \
    -> RedirectResponse:
    global g_session_data
    g_session_data = handle_user_signup(session_data = g_session_data,
                                        username = username,
                                        firstname = first_name)
    return RedirectResponse(url = "/login", status_code = status.HTTP_303_SEE_OTHER)


@app.get("/login")
async def get_login(request: Request) -> Response:
    if g_session_data.username:
        return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request, username: str = Form(...)) -> Response:
    global g_session_data
    if username in g_session_data.users:
        g_session_data = handle_user_login(session_data = g_session_data, username = username)
        return RedirectResponse(url = "/home", status_code = status.HTTP_303_SEE_OTHER)
    else:
        content = "<p>Invalid username. Try again or <a href='/signup'>sign up</a>.</p>"
        return HTMLResponse(content = content, status_code = 400)
    

@app.get("/logout")
def logout(request: Request) -> RedirectResponse:
    global g_session_data
    g_session_data.reset()
    return RedirectResponse(url = "/login", status_code = status.HTTP_303_SEE_OTHER)


@app.post("/set-language")
def set_language(request: Request, language: str = Form(...)) -> RedirectResponse:
    global g_session_data
    if g_session_data.username:
        print(f"/set-language: setting language to {language}")
        g_session_data.language = language.lower()
        g_session_data.all_levels = get_all_levels(language)
        return RedirectResponse(url = "/home", status_code = status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url = "/login", status_code = status.HTTP_303_SEE_OTHER)


@app.get("/choose-instruction-lang")
async def get_instruction_lang(request: Request) -> Response:
    if g_session_data.username:
        return templates.TemplateResponse("instruction-lang.html", 
                                          {"request": request, "levels": g_session_data.all_levels})
    else:
        return RedirectResponse(url = "/login", status_code = status.HTTP_303_SEE_OTHER)


@app.post("/set-instruction-lang")
def set_instruction_lang(request: Request, instructionlang: str = Form(...), 
                         targetlevel: str = Form(...)) -> RedirectResponse:
    global g_session_data
    g_session_data.instruction_language = instructionlang.lower()
    g_session_data.target_level = targetlevel.lower()
    return RedirectResponse(url = "/learning", status_code = status.HTTP_303_SEE_OTHER)


@app.get("/choose-backup-lang")
async def get_backup_lang(request: Request) -> Response:
    if g_session_data.username:
        return templates.TemplateResponse("backup-lang.html", 
                                          {"request": request, "levels": g_session_data.all_levels})
    else:
        return RedirectResponse(url = "/login", status_code = status.HTTP_303_SEE_OTHER)


@app.post("/set-backup-lang")
def set_backup_lang(request: Request, backuplang: str = Form(...), currentlevel: str = Form(...)) \
    -> RedirectResponse:
    global g_session_data
    g_session_data.backup_language = backuplang.lower()
    g_session_data.current_level = currentlevel.lower()
    return RedirectResponse(url = "/conversation", status_code = status.HTTP_303_SEE_OTHER)


@app.get("/learning")
async def get_learning_mode(request: Request) -> Response:
    if g_session_data.username:
        return templates.TemplateResponse("learning.html", 
                                          {"request": request, "language": g_session_data.language})
    else:
        return RedirectResponse(url = "/login", status_code = status.HTTP_303_SEE_OTHER)


@app.post("/save-learning")
def save_learning_mode(request: Request) -> JSONResponse:
    res = save_learning_info_to_profile(g_session_data)
    if res["success"]:
        return JSONResponse(status_code=200, content={"message": res["message"]})
    else:
        return JSONResponse(status_code=500, content={"message": res["message"]})


@app.websocket("/ws-learning")
async def websocket_endpoint_learning(websocket: WebSocket) -> None:
    global g_session_data

    await websocket.accept()
    g_session_data.learning_schema = "random-sample"### dummy

    info = get_learning_endpoint_info(g_session_data)

    engine = get_engine(info = info, engine_id = LEARNING_ENGINE, model_id = LEARNING_MODEL)
    tutor = LearningKani(user_profile = g_session_data.profile, 
                         engine = engine,
                         system_prompt = info.system_prompt)

    g_session_data.grammar_to_teach = info.grammar_to_teach
    g_session_data.engine = engine
    g_session_data.tutor = tutor

    try:
        while True:
            try:
                await websocket.receive()
            except WebSocketDisconnect:
                print("/ws-learning: webSocket disconnected")
                break
            user_input = handle_websocket_input(websocket)
            handle_learning_round(websocket = websocket, 
                                  tutor = tutor,
                                  user_input = user_input)

    except WebSocketDisconnect:
        print("/ws-learning: client disconnected")
    finally:
        await clean_up(engine)


@app.get("/conversation")
async def get_conversation_mode(request: Request) -> Response:
    if g_session_data.username:
        return templates.TemplateResponse("conversation.html", {"request": request})
    else:
        return RedirectResponse(url = "/login", status_code = status.HTTP_303_SEE_OTHER)


@app.post("/save-conversation")
async def save_conversation_mode(request: Request) -> JSONResponse:
    global g_session_data
    try:
        res = save_chat_info_to_profile(g_session_data)
        if res["success"]:
            return JSONResponse(status_code=200, content={"message": res["message"]})
        else:
            return JSONResponse(status_code=500, content={"message": res["message"]})
    
    finally:
        engine = g_session_data.engine
        await clean_up(engine)
    


@app.websocket("/ws-conversation")
async def websocket_endpoint_conversation(websocket: WebSocket) -> None:
    global g_session_data
    await websocket.accept()

    info = get_conversation_endpoint_info(g_session_data)
    engine = get_engine(info = info, engine_id = CHAT_ENGINE, model_id = CHAT_MODEL)
    tutor = ConversationKani(user_profile = g_session_data.profile,
                             engine = engine,
                             system_prompt = info.system_prompt,
                             desired_response_tokens = info.desired_response_tokens)

    g_session_data.engine = engine
    g_session_data.tutor = tutor

    rounds = 0
    g_session_data.user_interests = [g_session_data.profile["interests"]]
    g_session_data.user_info = [g_session_data.profile["personal-info"]]
    try:
        while True:
            if rounds % 16 == 0 and rounds != 0:
                tutor = summarize_chat_history(tutor = tutor, language = info.language)
            
            res = await handle_websocket_input(websocket)
            if not res["success"]:
                return JSONResponse(status_code = 500, 
                                    content = {"error": res["error"]})
            user_input = res["user_input"]
            
            g_session_data = await handle_chat_round(websocket = websocket, 
                                                     session_data = g_session_data,
                                                     tutor = tutor,
                                                     user_input = user_input)
            rounds += 1

    except WebSocketDisconnect:
        print("/ws-conversation: Client disconnected")
    finally:
        await clean_up(engine)
        

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)) -> JSONResponse:
    file_location = f"{ROOT_TEMP_DATA}{file.filename}"
    print(f"Uploaded audio file to {file_location}")
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return JSONResponse(content = {"status": "success"})
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host = APP_IP, port = APP_PORT)