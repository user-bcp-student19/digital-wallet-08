from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Callable

import copilot
from copilot.generated.rpc import PermissionDecisionReject
from copilot.session_events import (
    AssistantMessageData,
    AssistantMessageDeltaData,
    AssistantReasoningDeltaData,
    AssistantUsageData,
    SessionErrorData,
    ToolExecutionStartData,
)

HEARTBEAT_SECONDS = 15
_listener: Callable[[str, dict], None] | None = None


def set_progress_listener(listener: Callable[[str, dict], None] | None) -> None:
    """Registra un callback (kind, info) que recibe el progreso en vivo de cada llamada al modelo."""
    global _listener
    _listener = listener


def _emit(kind: str, **info: Any) -> None:
    if _listener is not None:
        try:
            _listener(kind, info)
        except Exception:
            pass  # el progreso nunca debe romper la llamada al modelo


def prompt_text(messages: Any) -> str:
    if isinstance(messages, str):
        return messages
    parts = []
    for message in messages:
        if isinstance(message, dict):
            role, content = message.get("role", "user"), message.get("content", "")
        else:
            role, content = message.type, message.content
        if isinstance(content, list):
            content = "\n".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )
        parts.append(f"[{role.upper()}]\n{content}")
    return "\n\n".join(parts)


async def complete(prompt: str, model: str, timeout: float = 600) -> str:
    def deny_permission(*_: Any) -> PermissionDecisionReject:
        return PermissionDecisionReject(feedback="El laboratorio solo solicita texto al modelo.")

    logged_in = os.getenv("COPILOT_USE_LOGGED_IN_USER", "true").lower() in {"true", "1", "yes", "s"}
    start = time.time()

    def on_event(event: Any) -> None:
        data = event.data
        if isinstance(data, AssistantMessageDeltaData):
            _emit("text", delta=data.delta_content or "", elapsed=time.time() - start)
        elif isinstance(data, AssistantReasoningDeltaData):
            _emit("reasoning", delta=data.delta_content or "", elapsed=time.time() - start)
        elif isinstance(data, ToolExecutionStartData):
            _emit("tool", name=str(getattr(data, "tool_name", "?")))
        elif isinstance(data, AssistantUsageData):
            _emit("usage", model=data.model, input_tokens=data.input_tokens, output_tokens=data.output_tokens,
                  ttft=data.time_to_first_token, duration=data.duration)
        elif isinstance(data, SessionErrorData):
            _emit("error", message=str(getattr(data, "message", data)))

    async def heartbeat() -> None:
        while True:
            await asyncio.sleep(HEARTBEAT_SECONDS)
            _emit("wait", elapsed=time.time() - start)

    _emit("start", model=model, prompt_chars=len(prompt))
    beat = asyncio.create_task(heartbeat())
    try:
        async with copilot.CopilotClient(use_logged_in_user=logged_in) as client:
            async with await client.create_session(
                model=model,
                reasoning_effort=os.getenv("COPILOT_REASONING_EFFORT", "high"),
                available_tools=[], on_permission_request=deny_permission,
                system_message={"mode": "replace", "content":
                    "Sigue las instrucciones del historial proporcionado por el laboratorio. "
                    "Devuelve texto o archivos en el formato solicitado, sin ejecutar herramientas."},
                skip_custom_instructions=True,
                working_directory=os.getcwd(),
                streaming=True,
            ) as session:
                session.on(on_event)
                event = await session.send_and_wait(prompt, timeout=timeout)
                if event is None or not isinstance(event.data, AssistantMessageData) or not event.data.content:
                    raise RuntimeError("Copilot terminó sin devolver una respuesta de texto.")
                _emit("end", chars=len(event.data.content), elapsed=time.time() - start)
                return event.data.content
    except Exception as exc:
        _emit("error", message=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        beat.cancel()


def complete_sync(messages: Any, model: str, timeout: float = 600) -> str:
    return asyncio.run(complete(prompt_text(messages), model, timeout))
