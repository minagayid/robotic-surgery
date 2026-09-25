"""Optional loopback-only OpenAI-compatible client for advisory text.

The client is intentionally not imported by the motion runtime. A response is
untrusted text and has no path to contracts, safety decisions, or actuation.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from .context import CompactionDecision, ContextCompactionPolicy


_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


@dataclass(frozen=True)
class LocalModelClient:
    endpoint: str
    model: str = "gpt-oss-20b"
    api_key: str = ""
    timeout: int = 30
    context_policy: ContextCompactionPolicy = field(default_factory=ContextCompactionPolicy)

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model must not be empty")
        if self.timeout < 1 or self.timeout > 300:
            raise ValueError("timeout must be between 1 and 300 seconds")
        if self.endpoint:
            parsed = urllib.parse.urlparse(self.endpoint)
            if parsed.scheme not in {"http", "https"} or parsed.hostname not in _LOCAL_HOSTS:
                raise ValueError("local model endpoint must use a loopback host")

    @property
    def available(self) -> bool:
        return bool(self.endpoint)

    @property
    def chat_url(self) -> str:
        if not self.endpoint:
            raise RuntimeError("local model is not configured")
        base = self.endpoint.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/v1"):
            return base + "/chat/completions"
        return base + "/v1/chat/completions"

    @classmethod
    def from_env(cls) -> "LocalModelClient":
        try:
            timeout = int(os.getenv("ROBOTIC_SURGERY_LOCAL_LLM_TIMEOUT", "30"))
        except ValueError:
            timeout = 30
        return cls(
            endpoint=os.getenv("ROBOTIC_SURGERY_LOCAL_LLM_BASE_URL", "").strip(),
            model=os.getenv("ROBOTIC_SURGERY_LOCAL_LLM_MODEL", "gpt-oss-20b").strip(),
            api_key=os.getenv("ROBOTIC_SURGERY_LOCAL_LLM_API_KEY", ""),
            timeout=timeout,
        )

    def context_budget(self, prompt: str, *, system: str = "") -> CompactionDecision:
        return self.context_policy.assess_text(system, prompt)

    def complete(self, prompt: str, *, system: str = "") -> str:
        if not self.available:
            raise RuntimeError("local model is not configured")
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        budget = self.context_budget(prompt, system=system)
        if budget.compaction_required:
            raise RuntimeError(
                "advisory context compaction is required before continuing "
                f"(estimated_ratio={budget.usage_ratio:.3f})"
            )
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        body = json.dumps({"model": self.model, "messages": messages, "temperature": 0.0}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(self.chat_url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data: Any = json.loads(response.read().decode("utf-8"))
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("local model returned an invalid chat-completions response") from exc
        if not isinstance(content, str) or not content.strip():
            raise ValueError("local model returned empty advisory text")
        return content.strip()
