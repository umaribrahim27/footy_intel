# footy_intel

A football intelligence API powered by a LangGraph agent, combining a vector knowledge base with live match data to answer natural language questions about football.

## What it does

footy_intel takes a natural language question and routes it through an agent that decides the best way to answer:

- **Tactics, players, history** → retrieves from a vector store of 195 curated football documents
- **Live scores** → hits a live football stats API
- **Recent results** → fetches today's matches from a live data source
- **Player lookup** → searches for a player's current club in real time

Every response includes the answer, which tool was used, tokens consumed, and latency — logged to a structured JSON file on every request.

## Architecture

```
User → FastAPI → LangGraph Agent → Tool routing decision
                                        ↓
                        ┌───────────────────────────────┐
                        │  retrieve_football_context     │  ← ChromaDB vector store
                        │  fetch_live_matches            │  ← Live stats API
                        │  fetch_matches_today           │  ← Live stats API
                        │  fetch_player_info             │  ← Live stats API
                        └───────────────────────────────┘
                                        ↓
                        Structured response + observability log
```

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Agent | LangGraph |
| LLM | GPT-4o-mini (swappable to DeepSeek) |
| Vector store | ChromaDB |
| Embeddings | ChromaDB default (all-MiniLM-L6-v2) |
| Live data | free-api-live-football-data (RapidAPI) |
| Containerization | Docker |
| Deployment | Azure Container Apps |
| Observability | Structured JSON logging (latency, tokens, tool used) |

## Key design decisions

**Why LangGraph over LangChain?**
LangGraph gives explicit control over the agent loop as a state machine. Each node does one thing — the agent decides, the tool executes, the state updates. This makes the system easier to extend, debug, and reason about than a chain-based approach.

**Why ChromaDB?**
Runs locally with zero infrastructure. For a portfolio project the priority is showing the retrieval pattern, not managing a vector database. In production this would be replaced with Pinecone or Azure AI Search.

**Why GPT-4o-mini over GPT-4o?**
Cost-to-quality tradeoff. For football Q&A, gpt-4o-mini is accurate enough and significantly cheaper. The model is configured in one place so swapping to DeepSeek or GPT-4o is a one-line change.

**Why a TTL cache on live API calls?**
The live stats API has a 50 request/day limit on the free tier. Caching responses for 2-10 minutes depending on data type prevents burning the quota on repeated identical queries. In production with a paid tier this would be relaxed.

**Why structured JSON logging?**
Flat text logs are hard to query. JSON logs can be ingested directly into monitoring tools like Datadog, Grafana, or Azure Monitor. Every request logs timestamp, question, answer preview, tokens used, latency, tool called, and status.

## Project structure

```
footy_intel/
├── main.py           # FastAPI app, request validation, observability
├── graph.py          # LangGraph agent, tool definitions, routing logic
├── vector_store.py   # ChromaDB setup, add and retrieve functions
├── live_stats.py     # Live API calls with TTL caching
├── seed_data.py      # 195 football documents across 8 categories
├── Dockerfile        # Container definition
├── requirements.txt  # Python dependencies
└── .env              # API keys (never committed)
```

## Running locally

```bash
# clone and set up environment
git clone https://github.com/umaribrahim27/footy_intel.git
cd footy_intel
conda create -n footy_bot python=3.11 -y
conda activate footy_bot
pip install -r requirements.txt

# add your keys
cp .env.example .env
# fill in OPENAI_API_KEY and RAPIDAPI_KEY

# seed the vector store
python seed_data.py

# run the server
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` to use the interactive API docs.

## Running with Docker

```bash
docker build -t footy_intel .
docker run -p 8000:8000 --env-file .env footy_intel
```

## Live deployment

The API is deployed on Azure Container Apps:

```
https://footy-intel-app.blackplant-0a9e640c.eastus.azurecontainerapps.io/docs
```

## Example queries

```json
{"question": "What matches were played today?"}
{"question": "How does Guardiola use inverted wingers?"}
{"question": "What team does Salah play for?"}
{"question": "Explain the offside rule"}
{"question": "What is gegenpressing?"}
{"question": "Are there any live matches right now?"}
```

## Observability

Every request is logged to `logs.json`:

```json
{
  "timestamp": "2026-05-24T20:57:44.281555",
  "question": "Haaland goals?",
  "answer_preview": "Erling Haaland scored an impressive 36 goals...",
  "tokens_used": 290,
  "latency_seconds": 2.172,
  "status": "success",
  "tool_used": "retrieve_football_context"
}
```

## What I would add with more time

- Evaluation layer to measure retrieval precision and answer quality
- Streaming responses for lower perceived latency
- CI/CD pipeline to auto-deploy on git push
- Upgrade to a paid stats API for historical and weekly match data
- Frontend interface for non-technical users
