import threading
import queue
import signal
import sys
import time
from ui import VynxApp
from tts import TTS
from settings import Settings
from memory_store import MemoryStore
from response_gen import generate_response
from audio_input import AudioInput

EVENTS = queue.Queue()
TTS_ENGINE = TTS()
SETTINGS = Settings.load()
MEMORY = MemoryStore('memory.json')
LISTENING = True
RUNNING = True

def on_text_submit(text: str):
    if text and text.strip():
        EVENTS.put(("user_text", text.strip()))

def toggle_listening():
    global LISTENING
    LISTENING = not LISTENING
    return LISTENING

def on_voice_text(text: str):
    if text and text.strip():
        EVENTS.put(("user_text", text.strip()))

def worker_loop(ui):
    while RUNNING:
        try:
            kind, payload = EVENTS.get(timeout=0.1)
        except queue.Empty:
            continue
        if kind == "sys_cmd":
            if payload.get("type") == "toggle_listening":
                state = toggle_listening()
                ui.set_listening_state(state)
            elif payload.get("type") == "quit":
                break
            continue
        if kind == "user_text":
            if not LISTENING:
                ui.toast("Listening is OFF")
                continue
            user_text = payload
            ui.add_chat_bubble(user_text, role="user")
            try:
                reply = generate_response(user_text, SETTINGS, MEMORY)
            except Exception as e:
                reply = f"(error) {e}"
            ui.add_chat_bubble(reply, role="assistant")
            TTS_ENGINE.speak(reply)

def on_settings_changed(s: Settings):
    global SETTINGS
    SETTINGS = s
    SETTINGS.save()
    TTS_ENGINE.set_voice(voice_id=SETTINGS.tts_voice_id, rate=SETTINGS.tts_rate, volume=SETTINGS.tts_volume)

def on_quit(ui, audio):
    global RUNNING
    RUNNING = False
    EVENTS.put(("sys_cmd", {"type": "quit"}))
    try:
        audio.stop()
    except Exception:
        pass
    try:
        TTS_ENGINE.shutdown()
    except Exception:
        pass
    ui.close()
    sys.exit(0)

def main():
    global LISTENING
    app = VynxApp(on_send=on_text_submit, on_toggle=lambda: EVENTS.put(("sys_cmd", {"type": "toggle_listening"})), on_settings_saved=on_settings_changed)
    app.set_listening_state(LISTENING)
    TTS_ENGINE.set_voice(voice_id=SETTINGS.tts_voice_id, rate=SETTINGS.tts_rate, volume=SETTINGS.tts_volume)
    worker = threading.Thread(target=worker_loop, args=(app,), daemon=True)
    worker.start()
    audio = AudioInput(device_name=SETTINGS.mic_device, wake_word=SETTINGS.wake_word, callback=on_voice_text)
    try:
        audio.start()
    except Exception as e:
        app.toast(f"Mic error: {e}")
    def handle_sig(*_):
        on_quit(app, audio)
    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)
    app.on_close(lambda: on_quit(app, audio))
    app.run()

if __name__ == "__main__":
    main()
