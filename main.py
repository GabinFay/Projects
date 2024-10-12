import os
import json
import pyaudio
from vosk import Model, KaldiRecognizer
import pyttsx3

# Initialize text-to-speech
engine = pyttsx3.init()

# Function to convert text to speech
def speak_text(text):
    engine.say(text)
    engine.runAndWait()

# Function to listen for voice activation word and process LLM request
def listen_for_command():
    # Load Vosk model
    model = Model("vosk-model-small-en-us-0.15")
    recognizer = KaldiRecognizer(model, 16000)

    # Set up PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()

    print("Listening...")
    while True:
        data = stream.read(4000)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result["text"]
            print(text.lower())
            
            # if "activation_word" in text.lower():
            #     print("Activation word detected!")
            #     # Listen for the command
            #     command = ""
            #     while not command:
            #         data = stream.read(4000)
            #         if recognizer.AcceptWaveform(data):
            #             command_result = json.loads(recognizer.Result())
            #             command = command_result["text"]
                
            #     print(f"Command: {command}")
            #     # Feed command to LLM here
            #     # response = llm.process(command)
            #     # speak_text(response)
            #     break

    stream.stop_stream()
    stream.close()
    p.terminate()

while True:
    listen_for_command()
