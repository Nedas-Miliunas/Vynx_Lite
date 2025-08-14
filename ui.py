import math
import customtkinter as ctk
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class VynxVisualizer(ctk.CTkCanvas):
    def __init__(self, master, size=100, points_count=500, **kwargs):
        super().__init__(master, width=size, height=size, bg="#000000", highlightthickness=0, **kwargs)
        self.size = size
        self.radius = size // 2 - 10
        self.center = (size // 2, size // 2)
        self.points_count = points_count

        self.base_points = [
            (
                self.center[0] + self.radius * math.cos(2 * math.pi * i / points_count),
                self.center[1] + self.radius * math.sin(2 * math.pi * i / points_count)
            )
            for i in range(points_count)
        ]

        self.lines = []
        self.phase = 0
        self.state = "waiting"

        self.current_amplitude = 0
        self.target_amplitude = 0

        self.current_phase_speed = 0
        self.target_phase_speed = 0

        self.max_amplitude = 4
        self.easing = 0.1

        self.draw_static_circle()
        self.animate()

    def draw_static_circle(self):
        self.delete("all")
        self.lines = []
        for i in range(self.points_count):
            p1 = self.base_points[i]
            p2 = self.base_points[(i + 1) % self.points_count]
            line = self.create_line(*p1, *p2, fill="#A020F0")
            self.lines.append(line)

    def update_animation(self):
        self.current_amplitude += (self.target_amplitude - self.current_amplitude) * self.easing
        self.current_phase_speed += (self.target_phase_speed - self.current_phase_speed) * self.easing

        self.phase += self.current_phase_speed

        new_points = []
        for i in range(self.points_count):
            angle = 2 * math.pi * i / self.points_count + math.pi
            offset = 0

            if self.state == "thinking":
                if math.pi <= angle % (2 * math.pi) <= 2 * math.pi:
                    offset = self.current_amplitude * math.sin(self.phase + i * 0.3)
            elif self.state == "talking":
                offset = self.current_amplitude * math.sin(self.phase + i * 0.3)

            new_x = self.center[0] + (self.radius + offset) * math.cos(angle)
            new_y = self.center[1] + (self.radius + offset) * math.sin(angle)
            new_points.append((new_x, new_y))

        for i in range(self.points_count):
            p1 = new_points[i]
            p2 = new_points[(i + 1) % self.points_count]
            if i < len(self.lines):
                self.coords(self.lines[i], *p1, *p2)

    def animate(self):
        try:
            self.update_animation()
        except Exception:
            pass
        self.after(50, self.animate)

    def set_state(self, new_state):
        if new_state not in ("waiting", "thinking", "talking"):
            raise ValueError(f"Invalid state: {new_state}")

        self.state = new_state

        state_settings = {
            "waiting": {"amplitude": 0, "phase_speed": 0},
            "thinking": {"amplitude": self.max_amplitude * 0.6, "phase_speed": 0.1},
            "talking": {"amplitude": self.max_amplitude, "phase_speed": 0.3},
        }

        settings = state_settings[new_state]
        self.target_amplitude = settings["amplitude"]
        self.target_phase_speed = settings["phase_speed"]


class VynxApp:
    def __init__(self, send_callback, voice_callback):
        self.root = tk.Tk()
        self.send_callback = send_callback
        self.voice_callback = voice_callback

        self.root.title("Vynx")
        self.root.attributes('-fullscreen', True)
        self.root.configure(background="#000000")

        self.input_mode = "text"

        self.chat_display = ctk.CTkTextbox(
            self.root, wrap="word", font=("Consolas", 14), state="disabled",
            border_width=1, border_color="#A020F0", fg_color="#0A0A0A", text_color="#C060FF"
        )
        self.chat_display.pack(padx=20, pady=(20, 10), fill="both", expand=True)

        input_frame = ctk.CTkFrame(self.root, fg_color="#000000")
        input_frame.pack(padx=20, pady=(0, 20), fill="x")

        self.input_field = ctk.CTkTextbox(
            input_frame, height=45, font=("Consolas", 14),
            border_width=1, border_color="#A020F0", fg_color="#0A0A0A", text_color="#C060FF"
        )
        self.input_field.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.input_field.bind("<Return>", self.on_enter)
        self.input_field.bind("<Shift-Return>", self.newline)

        self.visualizer = VynxVisualizer(input_frame, size=80)
        self.visualizer.pack(side="right", padx=(0, 10))

        self.mic_button = ctk.CTkButton(
            input_frame,
            text="🎤",
            width=45,
            height=45,
            command=self.toggle_input_mode,
            fg_color="#222222",
            hover_color="#444444",
            text_color="white",
            border_width=1,
            border_color="#A020F0",
            font=("Consolas", 20)
        )
        self.mic_button.pack(side="right", padx=(0, 10))

        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            width=100,
            height=45,
            command=self.send_callback,
            fg_color="#A020F0",
            hover_color="#C060FF",
            text_color="black",
            border_width=2,
            border_color="#8A2BE2",
        )
        self.send_button.pack(side="right")

    def toggle_input_mode(self):
        if self.input_mode == "text":
            self.input_mode = "voice"
            self.mic_button.configure(fg_color="#A020F0")
            self.voice_callback()
        else:
            self.input_mode = "text"
            self.mic_button.configure(fg_color="#222222")

    def set_mode(self, mode):
        self.visualizer.set_state(mode)

    def get_user_input(self):
        return self.input_field.get("1.0", "end").strip()

    def clear_input(self):
        self.input_field.delete("1.0", "end")

    def newline(self, event=None):
        self.input_field.insert("insert", "\n")
        return "break"

    def on_enter(self, event=None):
        if self.input_mode == "text":
            self.send_callback()
        else:
            self.voice_callback()
        return "break"

    def append_chat(self, sender, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{sender}: {message}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def replace_last_response(self, sender, new_message):
        self.chat_display.configure(state="normal")
        content = self.chat_display.get("1.0", "end")
        lines = content.strip().split("\n")

        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith(f"{sender}:"):
                lines[i] = f"{sender}: {new_message}"
                break
        else:
            lines.append(f"{sender}: {new_message}")

        self.chat_display.delete("1.0", "end")
        self.chat_display.insert("1.0", "\n".join(lines) + "\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def mainloop(self):
        self.root.mainloop()
