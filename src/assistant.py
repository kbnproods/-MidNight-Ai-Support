from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from dotenv import load_dotenv
from groq import Groq


DEFAULT_PERSONA_PATH = Path(__file__).resolve().parent.parent / "config" / "persona.md"


@dataclass
class AssistantConfig:
    """Runtime configuration for the Groq-powered assistant."""

    api_key: str
    model: str = "llama-3.1-8b-instant"
    persona_path: Path = DEFAULT_PERSONA_PATH
    max_tokens: int | None = None

    @classmethod
    def load(cls) -> "AssistantConfig":
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Create an API key in the Groq Console and "
                "set it in your environment or a .env file."
            )

        persona_path_env = os.getenv("GROQ_PERSONA_PATH")
        persona_path = Path(persona_path_env).expanduser() if persona_path_env else DEFAULT_PERSONA_PATH

        model = os.getenv("GROQ_MODEL", cls.model)
        max_tokens_str = os.getenv("GROQ_MAX_TOKENS")
        max_tokens = int(max_tokens_str) if max_tokens_str else None

        return cls(
            api_key=api_key,
            model=model,
            persona_path=persona_path,
            max_tokens=max_tokens,
        )


def load_persona(persona_path: Path) -> str:
    if not persona_path.exists():
        raise FileNotFoundError(
            f"Persona file not found at {persona_path}. Set GROQ_PERSONA_PATH or create the file."
        )
    return persona_path.read_text(encoding="utf-8").strip()


def build_messages(persona: str, conversation: Iterable[tuple[str, str]]) -> List[dict[str, str]]:
    messages: List[dict[str, str]] = []
    if persona:
        messages.append({"role": "system", "content": persona})

    for role, content in conversation:
        messages.append({"role": role, "content": content})

    return messages


def main() -> int:
    try:
        config = AssistantConfig.load()
    except Exception as exc:  # noqa: BLE001 - display readable error to user
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    try:
        persona = load_persona(config.persona_path)
    except Exception as exc:
        print(f"Persona error: {exc}", file=sys.stderr)
        return 1

    client = Groq(api_key=config.api_key)
    print("Groq Assistant ready. Type '/exit' to quit or '/reset' to clear context.\n")

    conversation: List[tuple[str, str]] = []
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "/exit":
            print("Goodbye!")
            break

        if user_input.lower() == "/reset":
            conversation.clear()
            print("Conversation context cleared.\n")
            continue

        conversation.append(("user", user_input))
        messages = build_messages(persona, conversation)

        try:
            request_kwargs = {"model": config.model, "messages": messages}
            if config.max_tokens is not None:
                request_kwargs["max_tokens"] = config.max_tokens
            completion = client.chat.completions.create(**request_kwargs)
        except Exception as exc:  # noqa: BLE001 - surface API issues to user quickly
            print(f"API error: {exc}", file=sys.stderr)
            conversation.pop()
            continue

        assistant_message = completion.choices[0].message.content
        print(f"Assistant: {assistant_message}\n")
        conversation.append(("assistant", assistant_message))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
