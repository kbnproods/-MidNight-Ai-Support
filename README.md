# Groq Assistant Starter

This repo shows how to turn Groq's `llama-3.1-8b-instant` model into a role-driven assistant.
It covers local setup on Windows, persona customization, a dark "MidNight AI" web chat,
and the pathway to enterprise LoRA fine-tuning when you need deeper control.

## Prerequisites

- Python 3.10+
- A Groq Cloud account with an API key from the [Groq Console](https://console.groq.com/keys)
- Optional: Enterprise access if you plan to upload LoRA adapters

## Setup (Windows PowerShell)

1. **Clone or download this repo.**
2. **Create a virtual environment** (optional but recommended):
   ```powershell
   py -3 -m venv .venv
   .venv\Scripts\Activate
   ```
3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
4. **Provide your API key.** Pick one of the options below:
   - Set it for the current session:
     ```powershell
     $env:GROQ_API_KEY = "paste-your-key"
     ```
   - Persist it for future sessions (requires a new terminal window):
     ```powershell
     setx GROQ_API_KEY "paste-your-key"
     ```
   - Or create a `.env` file at the project root:
     ```text
     GROQ_API_KEY=paste-your-key
     GROQ_MODEL=llama-3.1-8b-instant
     ```

## Run the MidNight AI web chat

Launch the FastAPI server, which serves both the API and the dark search-style UI:

```powershell
uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload
```

Open <http://localhost:8000> in your browser to chat. The UI code lives in `web/index.html`
with supporting assets under `web/assets/`.

## Run the CLI assistant

```powershell
python -m src.assistant
```

Type your question after the `You:` prompt. The assistant keeps conversation
state until you type `/reset` or exit with `/exit` (or `Ctrl+C`).

## Customize the persona

Edit `config/persona.md` to describe the behavior you want. This file is used as the
system prompt at the start of every conversation. For power users you can:

- Point to a different persona file by setting `GROQ_PERSONA_PATH`.
- Override the base model with `GROQ_MODEL`.
- Set a `GROQ_MAX_TOKENS` limit to bound responses.

Consider keeping explicit style, tone, guardrails, and example outputs in the persona file
instead of jumping straight to fine-tuning.

## When you actually need fine-tuning

Groq currently offers **LoRA adapter inference** for enterprise-tier customers:

1. Train a LoRA adapter externally against the exact `llama-3.1-8b-instant` base model
   (e.g., using Hugging Face PEFT or Unsloth).
2. Zip the resulting `adapter_model.safetensors` and `adapter_config.json` files.
3. Upload the zip via `POST https://api.groq.com/openai/v1/files` with `purpose="fine_tuning"`.
4. Register the adapter with `POST https://api.groq.com/v1/fine_tunings` specifying `type="lora"`.
5. Use the returned model ID (looks like `ft:llama-3.1-8b-instant:...`) in place of the base model.

LoRA access is currently enterprise-only. [Contact Groq](https://groq.com/enterprise-access/)
if you need this capability.

## Ideas for richer behavior without fine-tuning

- Extend the script to prepend conversation-specific context (e.g., knowledge-base snippets).
- Add tool/function calling to let the assistant run actions and return results.
- Incorporate retrieval-augmented generation (RAG) so the assistant can cite your documents.
- Use structured output mode for workflows that expect JSON.

## Troubleshooting

- `Configuration error: GROQ_API_KEY is not set` → double-check the environment variable or `.env` file.
- `API error: 401` → the token is missing, revoked, or belongs to another project.
- Slow replies? Ensure you're targeting a Groq region near your users and keep prompts concise.

Happy building!
