import speech_recognition as sr 
import threading
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
import os
from concurrent.futures import ThreadPoolExecutor
import requests
import io
from pydub import AudioSegment
from pydub.playback import play
from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

class LiveSpeechRecognition:
    def __init__(self, trigger_word: str = "bob", personality: str = "You're a nice guy called bob"): # Change the personality to whatever you want and the trigger word to whatever you want.
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.console = Console()
        self.groq_client = None
        self.trigger_word = trigger_word.lower()
        self.personality = personality
        self.layout = Layout()
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        self.memory = []
        self._initialize_layout()
        self._initialize_ai_client()
        self.is_processing = False
        self.stop_requested = False
        self.transcription_history = []
        self.error_log = []

    def _initialize_layout(self) -> None:
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["main"].split_row(
            Layout(name="input", ratio=1),
            Layout(name="output", ratio=1)
        )

    def _initialize_ai_client(self) -> None:
        if GROQ_AVAILABLE:
            try:
                api_key = os.getenv("GROQ_API_KEY")
                self.groq_client = Groq(api_key=api_key)
                self.console.print("Groq client initialized successfully.", style="bold green")
            except Exception as e:
                self._fallback_ai_init_error(e)
        else:
            self.console.print("Groq library not available. Running in echo mode.", style="yellow")

    def _fallback_ai_init_error(self, error: Exception) -> None:
        self.console.print(f"Error initializing Groq client: {error}", style="bold red")
        self.console.print("Falling back to echo mode. Set GROQ_API_KEY for AI features.", style="yellow")

    def start_listening(self) -> None:
        self.is_listening = True
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def stop_listening(self) -> None:
        self.is_listening = False
        self.stop_requested = True
        self.console.print("Stopped listening.", style="bold green")

    def _listen_loop(self) -> None:
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)

        with Live(self.layout, refresh_per_second=4) as live:
            while self.is_listening:
                self._update_footer("Listening...")
                try:
                    audio = self._capture_audio(source)
                    self._process_audio(audio, live)
                except sr.WaitTimeoutError:
                    self._update_footer("Listening timed out, continuing...", "yellow")
                time.sleep(0.1)

    def _capture_audio(self, source) -> sr.AudioData:
        with self.microphone as source:
            return self.recognizer.listen(source, timeout=5, phrase_time_limit=5)

    def _process_audio(self, audio: sr.AudioData, live: Live) -> None:
        try:
            text = self.recognizer.recognize_google(audio)
            self._update_input(f"You said: {text}")
            self.transcription_history.append(text)
            if text.lower() == "stop":
                self.stop_requested = True
                self._update_footer("Stop requested. Finishing current process...", "yellow")
            elif not self.is_processing:
                self._process_input(text, live)
        except sr.UnknownValueError:
            self._update_footer("Could not understand audio", "yellow")
        except sr.RequestError as e:
            self._update_footer(f"Request error: {e}", "red")
            self.error_log.append(f"Request error: {e}")

    def _process_input(self, user_input: str, live: Live) -> None:
        if self.trigger_word in user_input.lower():
            if self.groq_client:
                self.is_processing = True
                self.thread_pool.submit(self._process_with_ai, user_input, live)
            else:
                self._echo_response(user_input)
        else:
            self._update_footer(f"Trigger word '{self.trigger_word}' not detected.", "yellow")

    def _process_with_ai(self, user_input: str, live: Live) -> None:
        self._update_footer("Processing with AI...", "cyan")
        self._update_spinner_output("Processing...")
        
        try:
            self.memory.append({"role": "user", "content": user_input})
            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": f"personality: {self.personality}"}] + self.memory,
                temperature=1,
                max_tokens=1024,
                top_p=1,
                stream=True,
                stop=None,
            )
            ai_response = ""
            for chunk in completion:
                if self.stop_requested:
                    break
                ai_response += chunk.choices[0].delta.content or ""
            if not self.stop_requested:
                self.memory.append({"role": "assistant", "content": ai_response})
                self._update_output(ai_response, "AI Response")
                self._speak_async(ai_response)
        except Exception as e:
            self._update_footer(f"AI processing error: {e}", "red")
            self._echo_response(user_input)
            self.error_log.append(f"AI processing error: {e}")
        finally:
            self._update_footer("AI processing complete.", "green")
            self.is_processing = False
            self.stop_requested = False

    def _speak_async(self, text: str) -> None:
        self.thread_pool.submit(self._speak, text)

    def _speak(self, text: str) -> None:
        try:
            url = "https://api.elevenlabs.io/v1/text-to-speech/vO7hjeAjmsdlGgUdvPpe" # Change this to whatever voice you want.
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": os.getenv("ELEVENLABS_API_KEY")
            }

            data = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }

            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                audio = AudioSegment.from_mp3(io.BytesIO(response.content))
                play(audio)
            else:
                self.console.print(f"Error in speech synthesis: {response.status_code}", style="bold red")
                self.error_log.append(f"Error in speech synthesis: {response.status_code}")
        except Exception as e:
            self.console.print(f"Error in speech synthesis: {e}", style="bold red")
            self.error_log.append(f"Error in speech synthesis: {e}")
        finally:
            self.is_processing = False

    def _echo_response(self, user_input: str) -> None:
        self._update_output(f"Echo: {user_input}", "Echo Response")

    def _update_footer(self, message: str, style: str = "blue") -> None:
        self.layout["footer"].update(Panel(message, style=f"bold {style}"))

    def _update_input(self, message: str) -> None:
        self.layout["input"].update(Panel(Text(message, style="green"), title="Input"))

    def _update_output(self, message: str, title: str) -> None:
        self.layout["output"].update(Panel(Text(message, style="cyan"), title=title))

    def _update_spinner_output(self, title: str) -> None:
        self.layout["output"].update(Panel(Spinner("dots"), title=title))

    def save_transcription_history(self, file_path: str) -> None:
        with open(file_path, 'w') as file:
            for line in self.transcription_history:
                file.write(f"{line}\n")
        self.console.print(f"Transcription history saved to {file_path}", style="bold green")

    def save_error_log(self, file_path: str) -> None:
        with open(file_path, 'w') as file:
            for error in self.error_log:
                file.write(f"{error}\n")
        self.console.print(f"Error log saved to {file_path}", style="bold red")

if __name__ == "__main__":
    recognizer = LiveSpeechRecognition()
    recognizer.start_listening()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        recognizer.stop_listening()
        recognizer.save_transcription_history("transcription_history.txt")
        recognizer.save_error_log("error_log.txt")