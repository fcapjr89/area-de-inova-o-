import sounddevice as sd
from playsound import playsound
import scipy.io.wavfile as wavfile

from pynput import keyboard
import numpy as np
import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from faster_whisper import WhisperModel
from openai import OpenAI



whisper_model = WhisperModel("small", 
                                compute_type="int8", 
                                cpu_threads=os.cpu_count(), 
                                num_workers=os.cpu_count())

load_dotenv()
client = OpenAI()

class VoiceRecorder:
    def __init__(self, file_path='recording.wav', 
                 sample_rate=16000):
        self.file_path = file_path
        self.sample_rate = sample_rate
        self.is_recording = False
        self.audio_data = []
        self.stream = None

        self.llm = ChatGroq(temperature=0, model_name="llama3-8b-8192")
        

    def start_recording(self):
        print("Recording started...")
        self.audio_data = []  # Reset audio data
        self.stream = sd.InputStream(samplerate=self.sample_rate, 
                                     channels=1, callback=self.audio_callback)
        self.stream.start()

    def stop_recording(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
        audio_np = np.concatenate(self.audio_data, axis=0)
        wavfile.write(self.file_path, self.sample_rate, audio_np)  # Save as WAV file

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status, "Audio callback status error.")
        self.audio_data.append(indata.copy())  # Append the recorded chunk of data

    def transcribe_audio(self):
        segments, _ = whisper_model.transcribe(self.file_path, language="pt")
        clean_prompt = "".join(segment.text for 
                           segment in segments).strip()
        return clean_prompt

    def on_press(self, key):
        try:
            if key.char == 'r':
                if not self.is_recording:
                    self.is_recording = True
                    self.start_recording()
                else:
                    self.is_recording = False
                    self.stop_recording()
                    transcript = self.transcribe_audio()
                    print("User:", transcript)

                    llm_response = self.llm.invoke(transcript).content
                    print("LLM:", llm_response)
                    self.speak(llm_response)

        except AttributeError:
            pass  # Handle special keys like shift, ctrl, etc.
        
    def speak(self, text):
        resposta = client.audio.speech.create(
            model='tts-1',
            voice='nova', # ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            input=text
        )
        resposta.stream_to_file("out.wav")
        # resposta.write_to_file('out.wav')
        playsound('out.wav')

    def start(self):

        print("Press 'r' to start/stop recording...")
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()

# Usage example:
voice_recorder = VoiceRecorder()  # No duration needed, as we stop on second keypress
voice_recorder.start()  # Press 'r' to start/stop recording