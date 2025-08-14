import threading
import speech_recognition as sr
import re
import time
import queue
from ui import VynxApp
from response_gen import generate_response

tts_queue = queue.Queue()
_engine = None
_engine_lock = threading.Lock()
_speaking_event = threading.Event()
_on_start_callback = None
_on_end_callback = None

def remove_emojis(text):
    emoji_pattern = re.compile("[" 
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def on_start(name):
    global _on_start_callback
    if _on_start_callback:
        try:
            _on_start_callback()
        except Exception:
            pass

def on_end(name, completed):
    global _speaking_event, _on_end_callback, _engine
    _speaking_event.set()
    try:
        if _engine:
            _engine.stop()  # Stop to reset engine state
    except Exception:
        pass
    if _on_end_callback:
        try:
            _on_end_callback()
        except Exception:
            pass

def tts_worker():
    global _engine, _speaking_event, _on_start_callback, _on_end_callback
    import pyttsx3
    _engine = pyttsx3.init()
    voices = _engine.getProperty('voices')
    if len(voices) > 2:
        _engine.setProperty('voice', voices[2].id)
    elif len(voices) > 0:
        _engine.setProperty('voice', voices[0].id)
    _engine.setProperty('rate', 175)
    _engine.setProperty('volume', 1.0)
    _engine.connect('started-utterance', on_start)
    _engine.connect('finished-utterance', on_end)

    while True:
        item = tts_queue.get()
        if item is None:
            break
        text, on_start_cb, on_end_cb = item
        _on_start_callback = on_start_cb
        _on_end_callback = on_end_cb
        _speaking_event.clear()
        try:
            with _engine_lock:
                _engine.say(text)
                _engine.runAndWait()
            _speaking_event.wait()  # Wait for the 'finished-utterance' callback
        except Exception:
            _speaking_event.set()
        finally:
            try:
                with _engine_lock:
                    _engine.stop()  # Ensure engine reset after every utterance
            except Exception:
                pass
        tts_queue.task_done()

def speak(text, on_start=None, on_end=None):
    cleaned_text = remove_emojis(text)
    tts_queue.put((cleaned_text, on_start, on_end))

_tts_thread = threading.Thread(target=tts_worker, daemon=True)
_tts_thread.start()

class VynxController:
    def __init__(self):
        self.app = VynxApp(send_callback=self.handle_send, voice_callback=self.toggle_voice_mode)
        self.state = "waiting"
        self.voice_mode = False
        self.listening_thread = None
        self.stop_listening_flag = threading.Event()
        self.listening_lock = threading.Lock()

    def set_state(self, mode: str):
        self.state = mode
        try:
            self.app.set_mode(mode)
        except Exception:
            pass

    def toggle_voice_mode(self):
        self.voice_mode = not self.voice_mode
        if self.voice_mode:
            self.app.append_chat("System", "🎤 Voice mode ON")
            self.start_listening_loop()
        else:
            self.app.append_chat("System", "🎤 Voice mode OFF")
            self.stop_listening()

    def start_listening_loop(self):
        with self.listening_lock:
            if not self.voice_mode:
                return
            if self.listening_thread and self.listening_thread.is_alive():
                return
            self.stop_listening_flag.clear()
            self.listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listening_thread.start()

    def stop_listening(self):
        with self.listening_lock:
            self.stop_listening_flag.set()

    def _listen_loop(self):
        recognizer = sr.Recognizer()
        try:
            mic = sr.Microphone()
        except Exception as e:
            self.app.append_chat("System", f"[Mic Init Error] {e}")
            return
        while not self.stop_listening_flag.is_set() and self.voice_mode:
            if self.state != "waiting":
                self.stop_listening_flag.wait(0.2)
                continue
            try:
                with mic as source:
                    self.app.append_chat("System", "🎤 Listening...")
                    recognizer.adjust_for_ambient_noise(source, duration=0.4)
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=8)
                try:
                    text = recognizer.recognize_google(audio)
                    if text.strip():
                        self.app.append_chat("You (voice)", text)
                        self.stop_listening_flag.set()
                        self.process_in_thread(text)
                        break
                except sr.UnknownValueError:
                    self.app.append_chat("System", "❓ Didn't catch that.")
                except sr.RequestError as e:
                    self.app.append_chat("System", f"Speech recognition error: {e}")
                    break
            except Exception as e:
                self.app.append_chat("System", f"[Mic Error] {e}")
                break

    def handle_send(self):
        user_input = self.app.get_user_input()
        if not user_input.strip():
            return
        self.app.append_chat("You", user_input)
        self.app.clear_input()
        self.process_in_thread(user_input)

    def process_in_thread(self, user_input):
        self.stop_listening()
        self.set_state("thinking")
        self.app.append_chat("Vynx", "I'm thinking...")
        threading.Thread(target=self.process_response, args=(user_input,), daemon=True).start()

    def process_response(self, user_input):
        response = generate_response(user_input)
        def on_speak_start():
            self.set_state("talking")
        def on_speak_end():
            self.set_state("waiting")
            if self.voice_mode:
                threading.Timer(0.25, self.start_listening_loop).start()
        try:
            self.app.replace_last_response("Vynx", response)
        except Exception:
            self.app.append_chat("Vynx", response)
        speak(response, on_start=on_speak_start, on_end=on_speak_end)

    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    controller = VynxController()
    controller.run()
