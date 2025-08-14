import subprocess
import re
from personality_config import VYNX_SYSTEM_PROMPT

conversation_history = []

MAX_TURNS = 10
MAX_PROMPT_LENGTH = 4000
MAX_WORDS_DEFAULT = 30


def clean_response(text: str) -> str:
    """Clean model response by stripping unwanted prefixes and trailing whitespace."""
    text = text.strip()
    if text.lower().startswith("vynx:"):
        text = text[len("vynx:"):].strip()
    return text


def truncate_if_too_long(text: str, max_words: int = MAX_WORDS_DEFAULT) -> str:
    """Truncate to the first sentence or limit words if too long."""
    words = text.split()
    if len(words) > max_words:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if sentences and sentences[0].strip():
            return sentences[0].strip()
        return " ".join(words[:max_words]).strip()
    return text


def build_prompt(history: list, user_input: str) -> str:
    """Build a compact prompt including system prompt and recent history."""
    hist_copy = history[-(MAX_TURNS * 2):].copy()
    hist_copy.append(f"User: {user_input.strip()}")
    prompt = f"{VYNX_SYSTEM_PROMPT.strip()}\n\n" + "\n".join(hist_copy) + "\nVynx:"
    if len(prompt) > MAX_PROMPT_LENGTH:
        prompt = prompt[-MAX_PROMPT_LENGTH:]
    return prompt


def generate_response(user_input: str) -> str:
    global conversation_history

    if user_input.lower().strip() in ("reset", "reset chat", "clear chat"):
        conversation_history.clear()
        return "Chat history cleared! How can I help you now? 😊"

    conversation_history.append(f"User: {user_input.strip()}")

    prompt = build_prompt(conversation_history, user_input)

    try:
        result = subprocess.run(
            ["ollama", "run", "mistral"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode != 0:
            return f"[Error] Mistral returned an error: {result.stderr.strip()}"

        response = clean_response(result.stdout)
        response = truncate_if_too_long(response)
        conversation_history.append(f"Vynx: {response}")

        if len(conversation_history) > (MAX_TURNS * 2 + 10):
            conversation_history = conversation_history[-(MAX_TURNS * 2 + 10):]

        return response

    except Exception as e:
        return f"[Exception] {e}"