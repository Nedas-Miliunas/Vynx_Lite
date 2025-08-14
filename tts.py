import threading
import queue
import time
import pyttsx3

class TTS:
    def __init__(self):
        self._engine = pyttsx3.init()
        self._queue = queue.Queue()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._loop, daemon=True)
        self._stop_current = threading.Event()
        self._shutdown = threading.Event()
        self._worker.start()

    def set_voice(self, voice_id=None, rate=None, volume=None):
        if voice_id is not None:
            self._engine.setProperty('voice', voice_id)
        if rate is not None:
            self._engine.setProperty('rate', int(rate))
        if volume is not None:
            self._engine.setProperty('volume', float(volume))

    def speak(self, text: str):
        with self._lock:
            self._stop_current.set()
            try:
                self._engine.stop()
            except Exception:
                pass
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
            self._stop_current.clear()
            self._queue.put(text)

    def stop(self):
        with self._lock:
            self._stop_current.set()
            try:
                self._engine.stop()
            except Exception:
                pass

    def shutdown(self):
        self._shutdown.set()
        self.stop()

    def _loop(self):
        while not self._shutdown.is_set():
            try:
                text = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if self._stop_current.is_set():
                continue
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                time.sleep(0.05)
