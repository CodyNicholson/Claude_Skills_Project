"""The DemoResult contract every demo endpoint returns, and a recorder that builds it."""

from __future__ import annotations

import time
from typing import Any, Callable


class Demo:
    """Collects the commands a demo ran and the checks it verified, then renders the result.

    with Demo("hello") as d:
        d.command("tool.call('x')")
        d.check("Returned x", value == "x", f"got {value!r}")
        d.data["value"] = value
    return d.result()
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.commands: list[str] = []
        self.checks: list[dict[str, Any]] = []
        self.data: dict[str, Any] = {}
        self._started = time.perf_counter()

    def __enter__(self) -> "Demo":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def command(self, text: str) -> None:
        self.commands.append(text)

    def check(self, name: str, passed: bool, detail: Any = "") -> None:
        self.checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    def attempt(self, command: str, fn: Callable[[], Any]) -> tuple[Any, str | None]:
        """Run a step that may fail on purpose (a pitfall demo) and record the real error it raises.

        value, error = d.attempt("client.get(missing_key)", lambda: client.get(missing_key))
        d.check("The wrong way fails with the documented error", error and "KeyError" in error, error)
        """
        self.command(command)
        try:
            return fn(), None
        except Exception as exc:  # the error is the lesson: show it, don't hide it
            error = f"{type(exc).__name__}: {exc}"
            self.command(f"  -> {error}")
            return None, error

    def result(self) -> dict[str, Any]:
        return {
            "demo": self.name,
            "commands": self.commands,
            "data": self.data,
            "checks": self.checks,
            "elapsedMs": round((time.perf_counter() - self._started) * 1000, 2),
        }


def clamp(value: int, low: int, high: int) -> int:
    """The site is public through the tunnel: bound every size, count and duration a visitor can pick."""
    return max(low, min(high, value))
