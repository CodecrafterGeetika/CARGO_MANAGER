import speech_recognition as sr
import pyttsx3
import subprocess

# Initialize text-to-speech engine
engine = pyttsx3.init()

def speak(text):
    """🔊 Convert text to speech"""
    engine.say(text)
    engine.runAndWait()

def listen_command():
    """🎤 Capture voice command"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Listening for command...")
        print("🎤 Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio).lower()
            print(f"✅ You said: {command}")
            return command
        except sr.UnknownValueError:
            speak("Sorry, I didn't understand that.")
        except sr.RequestError:
            speak("Sorry, the speech service is unavailable.")
        except sr.WaitTimeoutError:
            speak("No command detected. Please try again.")
        return None

def run_cli_command(command):
    """🛠️ Runs CLI command safely"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        speak("Command executed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        speak("Error executing the command.")
        print(f"❌ Command failed: {e}")
    except FileNotFoundError:
        speak("CLI script not found. Please check if cli.py exists.")
        print("❌ cli.py not found.")

def execute_voice_command(command):
    """🎯 Map voice commands to CLI commands"""
    if "add" in command:
        speak("Adding a cargo item. Please provide details.")
        run_cli_command(["python3", "cli.py", "add", "--id", "006", "--name", "Tool Kit",
                         "--width", "20", "--depth", "15", "--height", "10", "--mass", "5",
                         "--priority", "85", "--expiry", "2026-06-01", "--usage", "15",
                         "--zone", "Storage Bay"])

    elif "search" in command:
        speak("What item do you want to search for?")
        item_name = listen_command()
        if item_name:
            run_cli_command(["python3", "cli.py", "search", "--name", item_name])

    elif "retrieve" in command:
        speak("What is the item ID?")
        item_id = listen_command()
        if item_id:
            run_cli_command(["python3", "cli.py", "retrieve", "--id", item_id])

    elif "waste" in command:
        speak("Which item do you want to mark as waste?")
        item_id = listen_command()
        if item_id:
            run_cli_command(["python3", "cli.py", "waste", "--id", item_id])

    elif "logs" in command:
        speak("Fetching logs.")
        run_cli_command(["python3", "cli.py", "logs"])

    elif "exit" in command:
        speak("Are you sure you want to exit? Say yes or no.")
        confirmation = listen_command()
        if confirmation and "yes" in confirmation:
            speak("Goodbye!")
            exit()
        else:
            speak("Continuing...")

    else:
        speak("Invalid command. Try again.")

if __name__ == '__main__':
    while True:
        speak("Say a command, or say 'exit' to stop.")
        command = listen_command()
        if command:
            execute_voice_command(command)