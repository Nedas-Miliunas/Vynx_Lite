import threading
import time
import speech_recognition as sr

class AudioInput:
    def __init__(self, device_name=None, wake_word=None, callback=None):
        self.device_name = device_name
        self.wake_word = wake_word.lower() if wake_word else None
        self.callback = callback
        self.recognizer = sr.Recognizer()
        self.mic = None
        self.thread = None
        self.running = False

    def _find_device_index(self):
        if self.device_name is None:
            return None
        try:
            from speech_recognition import Microphone
            for i, name in enumerate(Microphone.list_microphone_names()):
                if self.device_name.lower() in name.lower():
                    return i
        except Exception:
            return None
        return None

    def start(self):
        if self.running:
            return
        idx = self._find_device_index()
        self.mic = sr.Microphone(device_index=idx)
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _loop(self):
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
        while self.running:
            try:
                with self.mic as source:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=8)
                try:
                    text = self.recognizer.recognize_google(audio, language="en-US")
                except Exception:
                    text = ""
                if text:
                    if self.wake_word:
                        if self.wake_word in text.lower():
                            cleaned = text.lower().replace(self.wake_word, "").strip()
                            if cleaned:
                                if self.callback:
                                    self.callback(cleaned)
                    else:
                        if self.callback:
                            self.callback(text)
            except Exception:
                time.sleep(0.2)
