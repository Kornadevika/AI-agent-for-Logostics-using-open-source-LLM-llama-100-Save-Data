<<<<<<< HEAD
<<<<<<< HEAD
# 🚛 LogiBot — Logistics AI Agent
> Route optimization & delivery delay chatbot powered by **Gemma 4** (Ollama) + **FastAPI**

---

## Project Structure

```
logistics_agent/
├── main.py                  # FastAPI backend (Ollama integration)
├── requirements.txt         # Python dependencies
├── data/
│   └── logistics_data.json  # Live logistics data (shipments, drivers, roads)
├── frontend/
│   └── index.html           # Chat UI (open directly in browser)
└── README.md
```

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | https://python.org |
| Ollama | latest | https://ollama.com |
| Gemma 4 model | any size | see below |

---

## Step 1 — Install & start Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows → download from https://ollama.com/download
```

Pull the Gemma 4 model (choose based on your RAM):

```bash
ollama pull gemma4          # 4B  — needs ~6 GB RAM  (default in this project)
ollama pull gemma4:12b      # 12B — needs ~14 GB RAM (more accurate)
ollama pull gemma4:27b      # 27B — needs ~32 GB RAM (best quality)
```

Start Ollama (if not already running):

```bash
ollama serve
```

Verify it works:
```bash
ollama run gemma4 "Hello, are you working?"
```

---

## Step 2 — Set up Python backend

```bash
cd logistics_agent

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Step 3 — Start the backend

```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Test the backend:
```bash
curl http://localhost:8000/health
# → {"status":"ok","model":"gemma4"}
```

---

## Step 4 — Open the frontend

Open `frontend/index.html` directly in your browser:
```bash
# macOS
open frontend/index.html

# Linux
xdg-open frontend/index.html

# Windows
start frontend/index.html
```

Or access via the backend (also serves it):
```
http://localhost:8000
```

---

## Updating logistics data

Edit `data/logistics_data.json` to add real shipment data.
The backend reloads data on every request — no restart needed.

For a production setup, replace `load_data()` in `main.py` with a database query:

```python
# Example: PostgreSQL
def load_data() -> dict:
    conn = psycopg2.connect(DATABASE_URL)
    # ... query your TMS tables
    return build_data_dict(conn)
```

---

## Changing the model

In `main.py`, change:
```python
OLLAMA_MODEL = "gemma4"      # change to gemma4:12b or gemma4:27b
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Backend + model status |
| GET | `/data` | Current logistics data |
| POST | `/chat` | Send message, get AI reply |

### Chat request format

```json
POST /chat
{
  "messages": [
    { "role": "user", "content": "Why is order #4821 delayed?" }
  ]
}
```

### Response

```json
{
  "reply": "Order ORD-4821 is delayed by 47 minutes due to heavy congestion on the A2 motorway near Hannover...",
  "model": "gemma4"
}
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Cannot connect to Ollama` | Run `ollama serve` in a terminal |
| `Model not found` | Run `ollama pull gemma4` |
| `CORS error` in browser | Backend already has CORS enabled — check it's running on port 8000 |
| Slow responses | Use `gemma4` (4B) instead of larger models, or add GPU |
| Port 8000 in use | `uvicorn main:app --port 8001` and update `API` in `index.html` |
=======
# AI-agent-for-Logostics-using-open-source-LLM-llama
>>>>>>> 53746c027a8ef159e84465174438cbcb2eaa3ab2
=======
# AI-agent-for-Logostics-using-open-source-LLM-llama-100-Save-Data
>>>>>>> 84549d22e0a511a955ece7ede9907e01b2972499
