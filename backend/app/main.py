from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router

app = FastAPI(title="Local RAG Pipeline")

app.add_middleware(
    CORSMiddleware,
    # Matches the dev server from localhost or from any private-LAN IP
    # (so a phone on the same network can reach it too), on its one
    # known port — not a wildcard, which would also accept an origin
    # from outside the LAN.
    allow_origin_regex=(
        r"^http://(localhost|127\.0\.0\.1"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}):5173$"
    ),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
