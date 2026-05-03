"""
LogiBot — Logistics AI Agent Backend
FastAPI + Ollama (Gemma 4) + logistics data context

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
"""

import json
import httpx
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ── Config ──────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "gemma4"           # small model for low memory systems
DATA_FILE       = Path(__file__).parent / "data" / "logistics_data.json"
FRONTEND_DIR    = Path(__file__).parent / "frontend"

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="LogiBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Data helpers ─────────────────────────────────────────────────────────────
def load_data() -> dict:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_system_prompt(data: dict) -> str:
    """Build a rich system prompt injecting live logistics data."""

    # Summarise active shipments
    shipment_lines = []
    for s in data["shipments"]:
        driver = next((d for d in data["drivers"] if d["id"] == s["driver_id"]), {})
        status = f"DELAYED {s['delay_minutes']}min — {s['delay_reason']}" \
                 if s["status"] == "DELAYED" else "ON TIME"
        shipment_lines.append(
            f"  • {s['id']}: {s['origin']} → {s['destination']} | "
            f"Driver: {driver.get('name','?')} | Status: {status} | "
            f"ETA: {s['current_eta']} | Priority: {s['priority']} | "
            f"Customer: {s['customer']}"
        )

    # Summarise road conditions
    road_lines = []
    for r in data["road_conditions"]:
        if r["condition"] != "CLEAR":
            road_lines.append(
                f"  • {r['road']} ({r['segment']}): {r['condition']} "
                f"+{r['impact_minutes']}min — {r['cause']}"
            )

    # Summarise drivers
    driver_lines = []
    for d in data["drivers"]:
        driver_lines.append(
            f"  • {d['name']} ({d['id']}): "
            f"{d['delays_this_week']} delays this week, "
            f"avg {d['avg_delay_minutes']}min, "
            f"{d['total_deliveries_week']} deliveries, "
            f"rating {d['rating']}/5.0, "
            f"location: {d['current_location']}, "
            f"hours today: {d['hours_driven_today']}/{d['max_hours']}"
        )

    # Active alerts
    alert_lines = []
    for a in [x for x in data["alerts"] if not x["resolved"]]:
        alert_lines.append(f"  • [{a['severity']}] {a['message']}")

    # Fleet
    fleet = data["fleet"]

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"""You are LogiBot, an expert AI logistics operations agent for {data['company']}.
Today's date/time: {now_str}

You have real-time access to the following live operational data. Always use it to give specific, accurate answers.

=== ACTIVE SHIPMENTS ===
{chr(10).join(shipment_lines)}

=== ROAD CONDITIONS ===
{chr(10).join(road_lines) if road_lines else "  • All monitored roads clear"}

=== DRIVER PERFORMANCE ===
{chr(10).join(driver_lines)}

=== ACTIVE ALERTS ===
{chr(10).join(alert_lines) if alert_lines else "  • No active alerts"}

=== FLEET STATUS ===
  • Total trucks: {fleet['total_trucks']} | Active: {fleet['active']} | Maintenance: {fleet['in_maintenance']} | Breakdown: {fleet['breakdown']}
  • In maintenance: {', '.join(fleet['maintenance_trucks'])}

=== ROUTE OPTIONS ===
{json.dumps(data['routes'], indent=2)}

=== INSTRUCTIONS ===
- Answer questions concisely and specifically using the data above.
- For delay questions: state root cause, current delay, and suggest a concrete mitigation action.
- For route questions: recommend primary or alternate based on current road conditions.
- For driver questions: give honest performance assessment with numbers.
- Always mention order IDs, driver names, and exact ETAs — never be vague.
- If asked to take an action (reroute, alert driver), confirm you would execute it and describe what would happen.
- Keep responses focused — 3–5 sentences max unless a detailed breakdown is requested.
- Proactively flag any critical issues the dispatcher might have missed.
"""


# ── Request / Response models ─────────────────────────────────────────────────
class Message(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


class ChatResponse(BaseModel):
    reply: str
    model: str


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model": OLLAMA_MODEL}


@app.get("/data")
def get_data():
    """Return current logistics data (useful for dashboard)."""
    return load_data()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a conversation to Ollama (Gemma 4) with logistics context injected.
    The system prompt is rebuilt on every request so it always reflects
    the latest data from the JSON file (or your DB in production).
    """
    data = load_data()
    system_prompt = build_system_prompt(data)

    messages_payload = [
        {"role": m.role, "content": m.content}
        for m in request.messages
    ]

    ollama_body = {
        "model": OLLAMA_MODEL,
        "system": system_prompt,
        "messages": messages_payload,
        "stream": False,
        "options": {
            "temperature": 0.3,   # low temp for factual logistics answers
            "num_ctx": 8192,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=ollama_body
            )
            response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama. Is it running? → `ollama serve`"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama error: {e.response.text}"
        )

    result = response.json()
    reply_text = result.get("message", {}).get("content", "No response from model.")

    return ChatResponse(reply=reply_text, model=OLLAMA_MODEL)


# ── Serve frontend ────────────────────────────────────────────────────────────
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

    @app.get("/")
    def root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
