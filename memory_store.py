import json
import os

class MemoryStore:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write('[]')

    def add_fact(self, fact: str):
        facts = self.read_all()
        facts.append(fact)
        self._write_all(facts)

    def read_all(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def clear(self):
        self._write_all([])

    def _write_all(self, facts):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(facts, f, indent=2)

    def summarize_context(self, max_chars=800):
        data = " | ".join(self.read_all())
        return data[-max_chars:]
