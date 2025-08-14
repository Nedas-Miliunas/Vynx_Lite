import subprocess
from settings import Settings
from memory_store import MemoryStore
from personality_config import SYSTEM_PROMPT

def _ollama(prompt: str, model: str = "mistral") -> str:
    try:
        p = subprocess.run(["ollama", "run", model, prompt], capture_output=True, text=True, timeout=120)
        if p.returncode != 0:
            return p.stderr.strip() or "Ollama error"
        return p.stdout.strip()
    except FileNotFoundError:
        return "Ollama not found. Install Ollama and run: ollama pull mistral"
    except subprocess.TimeoutExpired:
        return "Model timeout"

def generate_response(user_text: str, settings: Settings, memory: MemoryStore) -> str:
    sys_prompt = settings.system_prompt or SYSTEM_PROMPT
    context = memory.summarize_context(max_chars=800) if settings.memory_enabled else ""
    prompt = f"SYSTEM:{sys_prompt}\nCONTEXT:{context}\nUSER:{user_text}\nASSISTANT:"
    return _ollama(prompt, settings.model_name)
