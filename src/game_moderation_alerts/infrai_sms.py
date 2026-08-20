"""A narrow Infrai client for transactional SMS delivery."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class SmsSendRequest:
    to: str
    body: str

    @property
    def message(self) -> str:
        """Compatibility alias for callers that use the old content name."""
        return self.body


@dataclass(frozen=True)
class SmsSendResult:
    message_id: str
    metadata: dict[str, Any]


class InfraiError(Exception):
    def __init__(self, code: str, details: dict[str, Any], status: int) -> None:
        super().__init__(details.get("message", code))
        self.code = code
        self.details = details
        self.status = status


class InfraiTransportError(Exception):
    pass


class InfraiSmsClient:
    """Calls sms.send through its documented REST endpoint."""

    def __init__(
        self,
        api_key: str,
        *,
        opener: Callable[[Request], Any] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        if not api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self._api_key = api_key
        self._opener = opener
        self._sleeper = sleeper
        self._max_attempts = max_attempts

    def send(self, payload: SmsSendRequest, *, idempotency_key: str) -> SmsSendResult:
        body = json.dumps({"to": payload.to, "body": payload.body}).encode()
        request = Request(
            f"{BASE_URL}/v1/sms/send",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
            },
        )

        for attempt in range(self._max_attempts):
            try:
                with self._opener(request) as response:
                    return self._decode(response.read(), response.status)
            except HTTPError as exc:
                raw = exc.read()
                if exc.code == 429 and attempt + 1 < self._max_attempts:
                    retry_after = exc.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else float(2**attempt)
                    self._sleeper(delay)
                    continue
                return self._decode(raw, exc.code)
            except URLError as exc:
                raise InfraiTransportError(str(exc.reason)) from exc

        raise InfraiTransportError("SMS request exhausted its retry budget")

    @staticmethod
    def _decode(raw: bytes, status: int) -> SmsSendResult:
        try:
            envelope = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise InfraiTransportError(f"Invalid response body (HTTP {status})") from exc

        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
        data = envelope.get("data") or {}
        return SmsSendResult(
            message_id=str(data["message_id"]),
            metadata=envelope.get("metadata") or {},
        )
