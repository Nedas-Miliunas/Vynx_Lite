import tkinter as tk
from tkinter import ttk, messagebox
from settings import Settings

class VynxApp:
    def __init__(self, on_send, on_toggle, on_settings_saved):
        self.on_send_cb = on_send
        self.on_toggle_cb = on_toggle
        self.on_settings_saved = on_settings_saved
        self.root = tk.Tk()
        self.root.title("Vynx Lite")
        self.root.geometry("840x640")
        self.root.minsize(720, 520)
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        top = ttk.Frame(self.root, padding=8)
        top.pack(side=tk.TOP, fill=tk.X)
        self.toggle_btn = ttk.Button(top, text="Listening: ON", command=self.on_toggle_cb)
        self.toggle_btn.pack(side=tk.LEFT)
        self.settings_btn = ttk.Button(top, text="Settings", command=self.open_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=6)
        self.status_var = tk.StringVar(value="")
        self.status_lbl = ttk.Label(top, textvariable=self.status_var, foreground="#666")
        self.status_lbl.pack(side=tk.RIGHT)
        mid = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        mid.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.chat = tk.Text(mid, wrap="word", state="disabled")
        self.chat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(mid, command=self.chat.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat["yscrollcommand"] = sb.set
        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        self.input_var = tk.StringVar()
        self.input = ttk.Entry(bottom, textvariable=self.input_var)
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input.bind("<Return>", lambda e: self.send())
        self.send_btn = ttk.Button(bottom, text="Send", command=self.send)
        self.send_btn.pack(side=tk.LEFT, padx=6)
        self.root.after(0, lambda: self.input.focus_set())
        self._on_close = None

    def add_chat_bubble(self, text, role="assistant"):
        self.chat.configure(state="normal")
        prefix = "You: " if role == "user" else "Vynx: "
        self.chat.insert("end", prefix + text + "\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def send(self):
        text = self.input_var.get()
        if not text.strip():
            return
        self.input_var.set("")
        self.on_send_cb(text)

    def set_listening_state(self, is_on: bool):
        self.toggle_btn.configure(text="Listening: ON" if is_on else "Listening: OFF")

    def toast(self, msg: str):
        self.status_var.set(msg)
        self.root.after(3500, lambda: self.status_var.set(""))

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("420x360")
        s = Settings.load()
        frm = ttk.Frame(win, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="Model name").grid(row=0, column=0, sticky="w")
        model_var = tk.StringVar(value=s.model_name)
        ttk.Entry(frm, textvariable=model_var).grid(row=0, column=1, sticky="ew")
        ttk.Label(frm, text="System prompt").grid(row=1, column=0, sticky="w")
        sys_var = tk.StringVar(value=s.system_prompt)
        ttk.Entry(frm, textvariable=sys_var).grid(row=1, column=1, sticky="ew")
        ttk.Label(frm, text="Mic device").grid(row=2, column=0, sticky="w")
        mic_var = tk.StringVar(value=s.mic_device if s.mic_device else "")
        ttk.Entry(frm, textvariable=mic_var).grid(row=2, column=1, sticky="ew")
        ttk.Label(frm, text="Wake word").grid(row=3, column=0, sticky="w")
        wake_var = tk.StringVar(value=s.wake_word if s.wake_word else "")
        ttk.Entry(frm, textvariable=wake_var).grid(row=3, column=1, sticky="ew")
        ttk.Label(frm, text="TTS voice id").grid(row=4, column=0, sticky="w")
        voice_var = tk.StringVar(value=s.tts_voice_id if s.tts_voice_id else "")
        ttk.Entry(frm, textvariable=voice_var).grid(row=4, column=1, sticky="ew")
        ttk.Label(frm, text="TTS rate").grid(row=5, column=0, sticky="w")
        rate_var = tk.IntVar(value=s.tts_rate)
        ttk.Entry(frm, textvariable=rate_var).grid(row=5, column=1, sticky="ew")
        ttk.Label(frm, text="TTS volume").grid(row=6, column=0, sticky="w")
        vol_var = tk.DoubleVar(value=s.tts_volume)
        ttk.Entry(frm, textvariable=vol_var).grid(row=6, column=1, sticky="ew")
        mem_var = tk.BooleanVar(value=s.memory_enabled)
        ttk.Checkbutton(frm, text="Enable memory", variable=mem_var).grid(row=7, column=0, columnspan=2, sticky="w")
        log_var = tk.BooleanVar(value=s.logs_enabled)
        ttk.Checkbutton(frm, text="Enable logs", variable=log_var).grid(row=8, column=0, columnspan=2, sticky="w")
        btns = ttk.Frame(frm)
        btns.grid(row=9, column=0, columnspan=2, pady=8, sticky="e")
        def save():
            ns = Settings(
                model_name=model_var.get().strip() or "mistral",
                system_prompt=sys_var.get(),
                tts_voice_id=voice_var.get().strip() or None,
                tts_rate=int(rate_var.get()),
                tts_volume=float(vol_var.get()),
                mic_device=mic_var.get().strip() or None,
                wake_word=wake_var.get().strip() or None,
                logs_enabled=bool(log_var.get()),
                memory_enabled=bool(mem_var.get())
            )
            self.on_settings_saved(ns)
            win.destroy()
        ttk.Button(btns, text="Save", command=save).pack(side=tk.RIGHT)
        frm.columnconfigure(1, weight=1)

    def on_close(self, cb):
        self._on_close = cb
        self.root.protocol("WM_DELETE_WINDOW", lambda: self._on_close())

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()
