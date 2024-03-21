"""
GPT Speech-to-Text and Text-to-Speech playground
## Whisper confidence score
## if any of the chunks have low confidence score, make user respeak entire chunk
## adjust temperature??
### but is there a way to just detect user's speaking as is?
### maybe tell the model that it is doing audio
## NEED TO SET RESPONSE FORMAT TO VERBOSE_JSON
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
import pyaudio
import wave
from pynput import keyboard
import threading

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "input.wav"

class AudioRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.recording_thread = None
        self.listener = keyboard.Listener(on_press=self.on_press)

    def on_press(self, key):
        if hasattr(key, 'char') and key.char == 'q':  # Exit condition
            if self.is_recording:
                self.stop_recording()
            self.listener.stop()  # Stop listening for key press, exits the program
        elif key == keyboard.Key.space:
            if self.is_recording:
                self.stop_recording()
                self.listener.stop()  # Stop listening for key press
            else:
                self.start_recording()

    def start_recording(self):
        self.is_recording = True
        self.frames = []  # Clear previous recordings
        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                      rate=RATE, input=True,
                                      frames_per_buffer=CHUNK)
        print("Recording started...")
        if not self.recording_thread:
            self.recording_thread = threading.Thread(target=self.record)
        self.recording_thread.start()

    def record(self):
        while self.is_recording:
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            self.frames.append(data)

    def stop_recording(self):
        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        print("Recording stopped.")
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print(f"File saved as {WAVE_OUTPUT_FILENAME}")

    def run(self):
        self.listener.start()
        self.listener.join()
        self.audio.terminate()


def record_audio():
    print("Press the space key to start/stop recording.")
    recorder = AudioRecorder()
    recorder.run()


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


def speech_to_text():
    record_audio()
    client = OpenAI()
    with open("input.wav", "rb") as audiofile:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audiofile
        )
        print("transcription: ", transcription.text)
        return transcription.text


async def language_chat(tutor):
    while (True):
        try:
            user_input = speech_to_text()
            response = await tutor.chat_round_str(user_input)
            print("Tutor: ", response)
            text_to_speech(response)
        except KeyboardInterrupt:
            await clean_up(tutor.engine)
            break
        except asyncio.exceptions.CancelledError:
            await clean_up(tutor.engine)
            break


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
    try:
        asyncio.run(language_chat(tutor))
    except Exception:
        exit(1)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    main()
