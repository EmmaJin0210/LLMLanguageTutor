"""
GPT Speech-to-Text and Text-to-Speech playground
"""
import os
import warnings
import asyncio
import numpy as np
from getpass import getpass
from openai import OpenAI
from kani import Kani, ChatMessage #, chat_in_terminal
from kani.engines.openai import OpenAIEngine
import simpleaudio as sa
import soundfile as sf
import sounddevice as sd
import pyautogui


def set_api_key():
    if 'OPENAI_API_KEY' not in os.environ:
        print("You didn't set your OPENAI_API_KEY on the command line.")
        os.environ['OPENAI_API_KEY'] = getpass("Please enter your OpenAI API Key: ")
    return os.environ['OPENAI_API_KEY']


def wav_to_16_bit(filepath):
    data, samplerate = sf.read(filepath)
    sf.write(filepath, data, samplerate, subtype='PCM_16')


def play_wav(filepath):
    wav_to_16_bit("output.wav")
    wave_obj = sa.WaveObject.from_wave_file(filepath)
    play_obj = wave_obj.play()
    play_obj.wait_done()


def text_to_speech(text):
    client = OpenAI()
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text,
    )
    response.stream_to_file("output.wav")
    play_wav("output.wav")


def record_audio(filepath, sample_rate=44100):
    print("Recording... Press 'Enter' to stop.")
    audio_data = []
    while True:
        try:
            chunk = sd.rec(1024, samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()
            audio_data.extend(chunk.flatten())
            if input() == "":
                break
        except KeyboardInterrupt:
            break
    sf.write(filepath, np.array(audio_data, dtype=np.int16), sample_rate)


def speech_to_text():
    record_audio("input.wav")
    client = OpenAI()
    with open("input.wav", "rb") as audiofile:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audiofile
        )
        return transcription.text


async def language_chat(tutor):
    while (True):
        if pyautogui.keyDown('q'):
            await clean_up(tutor.engine)
            break
        user_input = speech_to_text()
        response = await tutor.chat_round_str(user_input)
        print("Tutor: ", response)
        text_to_speech(response)



async def clean_up(engine):
    await engine.client.close()
    await engine.close()


def read_prompt(filepath):
    prompt = ""
    with open(filepath) as infile:
        for line in infile.readlines():
            prompt += line
    return prompt


def main():
    my_key = set_api_key()
    system_prompt = read_prompt("../testprompt.txt")
    chat_history = [ChatMessage.system(system_prompt)]

    engine = OpenAIEngine(my_key, model="gpt-4")
    tutor = Kani(engine, chat_history=chat_history)
    asyncio.run(language_chat(tutor))


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    main()
