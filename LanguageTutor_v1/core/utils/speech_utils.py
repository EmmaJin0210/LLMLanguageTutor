from openai import OpenAI
import simpleaudio as sa
import soundfile as sf
import pyaudio
import wave
from pynput import keyboard
import threading


### RECORD USER AUDIO
class AudioRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.recording_thread = None
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.stop_event = threading.Event()
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024
        self.WAVE_OUTPUT_FILENAME = "temp-data/input.wav"
        self.quit = False

    def on_press(self, key):
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

    def start_recording(self):
        self.is_recording = True
        self.frames = []  # Clear previous recordings
        self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                      rate=self.RATE, input=True,
                                      frames_per_buffer=self.CHUNK)
        print("Recording started...")
        self.stop_event.clear()  # Clear the stop event
        if not self.recording_thread or not self.recording_thread.is_alive():
            self.recording_thread = threading.Thread(target=self.record)
            self.recording_thread.start()

    def record(self):
        while not self.stop_event.is_set():
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            self.frames.append(data)
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None

    def stop_recording(self):
        self.is_recording = False
        self.stop_event.set()  # Signal the thread to stop
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join()  # Ensure thread is joined
        self.save_recording()
        print("Recording stopped.")

    def save_recording(self):
        wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print(f"File saved as {self.WAVE_OUTPUT_FILENAME}")

    def run(self):
        try:
            self.listener.start()
            print("Listener started")
            self.listener.join()  # Blocks here until listener stops
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.audio.terminate()
            print("Audio terminated")
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join()
                print("Thread joined")

def record_audio():
    print("Press the space key to start/stop recording. Press 'q' to quit.")
    recorder = AudioRecorder()
    recorder.run()
    print("Finished running")
    if recorder.quit:
        return 1
    return 0

class ExitProgram(Exception):
    def __init__(self, message="User wants to exit program"):
        self.message = message
        super().__init__(self.message)

async def speech_to_text():
    status = record_audio()
    if status == 1:
        raise ExitProgram()
    client = OpenAI()
    with open("temp-data/input.wav", "rb") as audiofile:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audiofile
        )
        print("transcription: ", transcription.text)
        return transcription.text

### TO-SPEECH BOT OUTPUT
def wav_to_16_bit(filepath):
    print("before write 1")
    data, samplerate = sf.read(filepath)
    print("before write 2")
    sf.write(filepath, data, samplerate, subtype='PCM_16')


def play_wav(filepath):
    wav_to_16_bit("temp-data/output.wav")
    wave_obj = sa.WaveObject.from_wave_file(filepath)
    play_obj = wave_obj.play()
    play_obj.wait_done()


def text_to_speech(text):
    client = OpenAI()
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text,
    )
    print("right before response")
    response.stream_to_file("temp-data/output.wav")
    play_wav("temp-data/output.wav")


def text_to_speech_web(text):
    client = OpenAI()
    filename = "output.wav"  # You might want to generate unique names
    file_path = f"core/temp-data/{filename}"
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text,
    )
    print("right before response")
    response.stream_to_file(file_path)
    return filename