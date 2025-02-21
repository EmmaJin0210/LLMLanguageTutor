from openai import OpenAI
import threading
from pynput import keyboard
from typing import Union
###### imports for audio ######
import simpleaudio as sa
import soundfile as sf
import pyaudio
import wave
###############################
from core.core_constants import TRANSCRIPTION_MODEL, TTS_MODEL
from appstuff.app_constants import ROOT_TEMP_DATA, \
FILENAME_AUDIO_INPUT, FILENAME_AUDIO_OUTPUT


### RECORD USER AUDIO
class AudioRecorder:
    def __init__(self) -> None:
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.recording_thread = None
        self.listener = keyboard.Listener(on_press = self.on_press)
        self.stop_event = threading.Event()
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024
        self.WAVE_OUTPUT_FILENAME = f"{ROOT_TEMP_DATA}{FILENAME_AUDIO_INPUT}"
        self.quit = False

    def on_press(self, key: Union[keyboard.Key, keyboard.KeyCode]) -> None:
        if hasattr(key, 'char') and key.char == 'q':
            self.quit = True
            self.stop_recording()
            self.listener.stop()
        elif key == keyboard.Key.space:
            if self.is_recording:
                self.stop_recording()
                print("stopped recording")
                self.listener.stop()
            else:
                self.start_recording()

    def start_recording(self) -> None:
        self.is_recording = True
        self.frames = []  # Clear previous recordings
        self.stream = self.audio.open(format = self.FORMAT, 
                                      channels = self.CHANNELS,
                                      rate = self.RATE, 
                                      input = True,
                                      frames_per_buffer = self.CHUNK)
        print("Recording started...")
        self.stop_event.clear()  # Clear the stop event
        if not self.recording_thread or not self.recording_thread.is_alive():
            self.recording_thread = threading.Thread(target=self.record)
            self.recording_thread.start()

    def record(self) -> None:
        while not self.stop_event.is_set():
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            self.frames.append(data)
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None

    def stop_recording(self) -> None:
        self.is_recording = False
        self.stop_event.set()  # Signal the thread to stop
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join()  # Ensure thread is joined
        self.save_recording()
        print("Recording stopped.")

    def save_recording(self) -> None:
        wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print(f"File saved as {self.WAVE_OUTPUT_FILENAME}")

    def run(self) -> None:
        try:
            self.listener.start()
            self.listener.join()  # Blocks here until listener stops
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.audio.terminate()
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join()


class ExitProgram(Exception):
    def __init__(self, message: str = "User wants to exit program"):
        self.message = message
        super().__init__(self.message)


def record_audio() -> None:
    print("Press the space key to start/stop recording. Press 'q' to quit.")
    recorder = AudioRecorder()
    recorder.run()
    if recorder.quit:
        return 1
    return 0


async def speech_to_text() -> str:
    status = record_audio()
    if status == 1:
        raise ExitProgram()
    client = OpenAI()
    with open(f"{ROOT_TEMP_DATA}{FILENAME_AUDIO_INPUT}", "rb") as audiofile:
        transcription = client.audio.transcriptions.create(
            model = TRANSCRIPTION_MODEL,
            file=audiofile
        )
        print("transcription: ", transcription.text)
        return transcription.text


### TO-SPEECH BOT OUTPUT
def wav_to_16_bit(filepath: str) -> None:
    data, samplerate = sf.read(filepath)
    sf.write(file = filepath, 
             data = data, 
             samplerate = samplerate, 
             subtype='PCM_16')


def play_wav(filepath: str) -> None:
    wav_to_16_bit(f"{ROOT_TEMP_DATA}{FILENAME_AUDIO_OUTPUT}")
    wave_obj = sa.WaveObject.from_wave_file(filepath)
    play_obj = wave_obj.play()
    play_obj.wait_done()


def text_to_speech(text: str) -> str:
    client = OpenAI()
    file_path = f"{ROOT_TEMP_DATA}{FILENAME_AUDIO_OUTPUT}"
    response = client.audio.speech.create(
        model = TTS_MODEL,
        voice = "onyx",
        input = text,
    )
    response.stream_to_file(file_path)
    return FILENAME_AUDIO_OUTPUT