import speech_recognition as sr
import pyttsx3
import requests

# Initialize text-to-speech engine
engine = pyttsx3.init()

def speak(text):
    """Convert text to speech"""
    engine.say(text)
    engine.runAndWait()

def listen_command():
    """Listen for a voice command and convert it to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Listening for command...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio).lower()
            print(f"✅ You said: {command}")
            return command
        except sr.UnknownValueError:
            speak("Sorry, I didn't understand that.")
            return None
        except sr.RequestError:
            speak("Sorry, the speech recognition service is unavailable.")
            return None
        except sr.WaitTimeoutError:
            speak("No command detected. Try again.")
            return None

def execute_voice_command(command):
    """Map voice commands to API calls"""
    if command is None:
        return

    base_url = "http://localhost:8000/api"
    
    if "add" in command:
        response = requests.post(f"{base_url}/add", json={
            "id": "001", "name": "Food Packet", "width": 10, "depth": 10, "height": 20,
            "mass": 5, "priority": 80, "expiry": "2025-05-20", "usage": 30, "zone": "Crew Quarters"
        })
        speak("Food Packet has been added.")

    elif "search" in command:
        response = requests.get(f"{base_url}/search", params={"name": "Food Packet"})
        data = response.json()
        if data['success']:
            speak(f"Found: {data['data']}")
        else:
            speak("Item not found.")

    elif "retrieve" in command:
        response = requests.post(f"{base_url}/retrieve", json={"id": "001"})
        speak(response.json()['message'])

    elif "waste" in command:
        response = requests.post(f"{base_url}/waste", json={"id": "001"})
        speak(response.json()['message'])

    elif "stop" in command or "exit" in command:
        speak("Stopping voice assistant. Goodbye!")
        exit(0)

    else:
        speak("Invalid command. Please try again.")

if __name__ == '__main__':
    speak("Voice command system initialized. Say a command.")
    
    while True:
        command = listen_command()
        if command:
            execute_voice_command(command)