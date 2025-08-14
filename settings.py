import json
import os
from dataclasses import dataclass, asdict

@dataclass
class Settings:
    model_name: str = "mistral"
    system_prompt: str = "You are Vynx, a friendly, concise, motivating assistant."
    tts_voice_id: str | None = None
    tts_rate: int = 180
    tts_volume: float = 1.0
    mic_device: str | None = None
    wake_word: str | None = None
    logs_enabled: bool = True
    memory_enabled: bool = False

    @classmethod
    def path(cls):
        return os.path.join(os.getcwd(), 'config.json')

    @classmethod
    def load(cls):
        p = cls.path()
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)
        s = cls()
        s.save()
        return s

    def save(self):
        with open(self.path(), 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2)
