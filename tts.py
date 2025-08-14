import pyttsx3
import re
import threading
import time

# Initialize a single engine instance and a lock — pyttsx3 is not always thread-safe if you init multiple times.
_engine = None
_engine_lock = threading.Lock()


def _init_engine():
    global _engine
    if _engine is None:
        try:
            _engine = pyttsx3.init()
        except Exception as e:
            _engine = None


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


def speak(text: str, on_start=None, on_end=None):
    """Speak text on a background thread. Uses a single engine instance and a lock.
    on_start and on_end are optional callbacks executed on TTS start/end."""
    def run():
        if on_start:
            try:
                on_start()
            except Exception:
                pass

        cleaned_text = remove_emojis(text)

        _init_engine()

        if _engine is None:
            print("[TTS Error] engine not available.")
            if on_end:
                try:
                    on_end()
                except Exception:
                    pass
            return

        try:
            with _engine_lock:
                voices = _engine.getProperty('voices')
                if len(voices) > 2:
                    _engine.setProperty('voice', voices[2].id)
                elif len(voices) > 0:
                    _engine.setProperty('voice', voices[0].id)

                _engine.setProperty('rate', 175)
                _engine.setProperty('volume', 1.0)

                _engine.say(cleaned_text)
                _engine.runAndWait()
                time.sleep(0.05)
        except Exception as e:
            print(f"[TTS Error] {e}")

        if on_end:
            try:
                on_end()
            except Exception:
                pass

    threading.Thread(target=run, daemon=True).start()
