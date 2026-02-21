"""
Unified LLM provider layer using LiteLLM.
Supports Gemini, Anthropic, and Ollama via a single interface.

Config is driven by environment variables:
  LLM_PROVIDER=gemini|anthropic|ollama
  LLM_MODEL=<model name>  (optional, has sensible defaults per provider)

  # Provider-specific keys (only need the one you're using):
  GEMINI_API_KEY=...
  ANTHROPIC_API_KEY=...
  OLLAMA_BASE_URL=https://your-ngrok-domain.ngrok-free.app  (for self-hosted)
  OLLAMA_AUTH_USER=...    (optional, if you set up basic auth on ngrok)
  OLLAMA_AUTH_PASS=...

  # Vision model (for invoice/document processing):
  LLM_VISION_MODEL=<model name>  (optional, defaults per provider)
"""
import os
import litellm
from litellm import completion, acompletion
import json
import base64
from typing import Optional

# ── Provider Config ──────────────────────────────────────────

PROVIDER_DEFAULTS = {
    "gemini": {
        "model": "gemini/gemini-2.5-flash",
        "vision_model": "gemini/gemini-2.5-flash",  # Gemini handles vision natively
    },
    "anthropic": {
        "model": "anthropic/claude-sonnet-4-20250514",
        "vision_model": "anthropic/claude-sonnet-4-20250514",
    },
    "ollama": {
        "model": "ollama/gemma3:12b",
        "vision_model": "ollama/llama3.2-vision:11b",
    },
}

def get_provider() -> str:
    return os.getenv("LLM_PROVIDER", "ollama").lower()

def get_model(vision: bool = False) -> str:
    provider = get_provider()
    defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["ollama"])
    if vision:
        return os.getenv("LLM_VISION_MODEL", defaults["vision_model"])
    return os.getenv("LLM_MODEL", defaults["model"])

def _get_api_base() -> Optional[str]:
    """Return api_base for Ollama, None for cloud providers."""
    provider = get_provider()
    if provider == "ollama":
        base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return base
    return None

def _configure_litellm():
    """One-time setup for LiteLLM."""
    litellm.drop_params = True  # Drop unsupported params instead of erroring
    # If using Ollama with basic auth via ngrok, set custom headers
    user = os.getenv("OLLAMA_AUTH_USER")
    pw = os.getenv("OLLAMA_AUTH_PASS")
    if user and pw:
        encoded = base64.b64encode(f"{user}:{pw}".encode()).decode()
        litellm.headers = {"Authorization": f"Basic {encoded}"}

_configure_litellm()

# ── Core Functions ───────────────────────────────────────────

async def chat(
    messages: list[dict],
    system: str = None,
    tools: list[dict] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    vision: bool = False,
) -> dict:
    """
    Send a chat completion request to whichever LLM provider is configured.

    Args:
        messages: OpenAI-format messages [{"role": "user", "content": "..."}]
        system: System prompt (prepended as a system message)
        tools: OpenAI-format tool definitions for function calling
        temperature: Sampling temperature
        max_tokens: Max tokens in response
        vision: If True, use the vision model (for image inputs)

    Returns:
        dict with keys: content, tool_calls, usage, raw_response
    """
    model = get_model(vision=vision)
    api_base = _get_api_base()

    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    kwargs = {
        "model": model,
        "messages": full_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if api_base:
        kwargs["api_base"] = api_base
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    try:
        response = await acompletion(**kwargs)
        choice = response.choices[0]

        return {
            "content": choice.message.content or "",
            "tool_calls": _extract_tool_calls(choice.message),
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            "raw_response": response,
        }
    except Exception as e:
        return {
            "content": f"LLM Error ({get_provider()}): {str(e)}",
            "tool_calls": [],
            "usage": {},
            "raw_response": None,
            "error": True,
        }


async def chat_with_vision(
    text_prompt: str,
    image_base64: str,
    mime_type: str = "image/png",
    system: str = None,
) -> dict:
    """
    Send an image + text prompt to the vision model.
    Used for invoice OCR, document extraction, etc.
    """
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": text_prompt},
            {"type": "image_url", "image_url": {
                "url": f"data:{mime_type};base64,{image_base64}"
            }},
        ],
    }]
    return await chat(messages=messages, system=system, vision=True)


def _extract_tool_calls(message) -> list[dict]:
    """Extract tool calls from response into a clean format."""
    if not hasattr(message, "tool_calls") or not message.tool_calls:
        return []
    calls = []
    for tc in message.tool_calls:
        args = tc.function.arguments
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                pass
        calls.append({
            "id": tc.id,
            "function": tc.function.name,
            "arguments": args,
        })
    return calls


# ── Convenience: complete tool calling loop ──────────────────

async def chat_with_tools(
    messages: list[dict],
    system: str,
    tools: list[dict],
    tool_executor: callable,
    max_rounds: int = 5,
) -> dict:
    """
    Run a full tool-calling loop:
    1. Send messages + tools to LLM
    2. If LLM returns tool_calls, execute them via tool_executor
    3. Append results, send back to LLM
    4. Repeat until LLM returns a text response (or max_rounds)

    Args:
        tool_executor: async function(name, args) -> result_string
    """
    current_messages = list(messages)

    for _ in range(max_rounds):
        result = await chat(
            messages=current_messages,
            system=system,
            tools=tools,
        )

        if result.get("error"):
            return result

        if not result["tool_calls"]:
            return result  # Final text response

        # Execute each tool call
        assistant_msg = result["raw_response"].choices[0].message
        current_messages.append({"role": "assistant", "content": assistant_msg.content, "tool_calls": [tc for tc in assistant_msg.tool_calls]})

        for tc in result["tool_calls"]:
            try:
                tool_result = await tool_executor(tc["function"], tc["arguments"])
                tool_result_str = json.dumps(tool_result) if isinstance(tool_result, (dict, list)) else str(tool_result)
            except Exception as e:
                tool_result_str = json.dumps({"error": str(e)})

            current_messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": tool_result_str,
            })

    return result  # Return last result if max rounds hit
