"""__LAB_NAME__ API. One endpoint per feature under /api/demos/*, each returning a DemoResult."""

from __future__ import annotations

from fastapi import FastAPI, Query

from .lab import Demo

app = FastAPI(title="__LAB_NAME__", docs_url="/api/docs", openapi_url="/api/openapi.json")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/demos/hello")
def hello(message: str = Query("hello", max_length=200), mistake: bool = False) -> dict:
    with Demo("hello") as d:
        if mistake:
            # A pitfall demo: do it the wrong way for real, show the genuine error, then the fix
            _, error = d.attempt(f"int({message!r})  # wrong: treats text as a number", lambda: int(message))
            d.check("The wrong way fails with the error the page describes", error is not None, error)
            d.data["error"] = error
        # Replace with a real call into __TOOL__
        reply = message.upper()
        d.command(f"upper({message!r})")
        d.check("Reply is the upper-cased message", reply == message.upper(), reply)
        d.data.update({"message": message, "reply": reply})
    return d.result()
