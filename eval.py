import json
import time
import mlflow
from graph import run_agent

# --- TEST SET ---
test_cases = [
    {
        "id": "e1",
        "question": "What matches were played today?",
        "expected_tool": "fetch_matches_today",
        "keywords": ["vs", "FT", "-"]
    },
    {
        "id": "e2",
        "question": "Are there any live matches right now?",
        "expected_tool": "fetch_live_matches",
        "keywords": []
    },
    {
        "id": "e3",
        "question": "What team does Haaland play for?",
        "expected_tool": "fetch_player_info",
        "keywords": ["manchester city", "city"]
    },
    {
        "id": "e4",
        "question": "What team does Salah play for?",
        "expected_tool": "fetch_player_info",
        "keywords": ["liverpool"]
    },
    {
        "id": "e5",
        "question": "Explain the tiki taka style of play",
        "expected_tool": "retrieve_football_context",
        "keywords": ["possession", "passing", "barcelona", "spain"]
    },
    {
        "id": "e6",
        "question": "What is gegenpressing?",
        "expected_tool": "retrieve_football_context",
        "keywords": ["press", "klopp", "possession", "liverpool"]
    },
    {
        "id": "e7",
        "question": "How does a false nine work?",
        "expected_tool": "retrieve_football_context",
        "keywords": ["drops", "space", "defenders", "messi"]
    },
    {
        "id": "e8",
        "question": "What is the offside rule?",
        "expected_tool": "retrieve_football_context",
        "keywords": ["defender", "goal", "position"]
    },
    {
        "id": "e9",
        "question": "How many Premier League titles has Manchester United won?",
        "expected_tool": "retrieve_football_context",
        "keywords": ["13", "thirteen"]
    },
    {
        "id": "e10",
        "question": "What team does De Bruyne play for?",
        "expected_tool": "fetch_player_info",
        "keywords": ["manchester city", "city"]
    }
]

# --- SCORING ---
def score_answer(question: str, answer: str, keywords: list[str]) -> dict:
    if not keywords:
        return {"keyword_score": 1.0, "note": "no keywords defined"}
    answer_lower = answer.lower()
    matched = [kw for kw in keywords if kw.lower() in answer_lower]
    score = len(matched) / len(keywords)
    return {
        "keyword_score": round(score, 2),
        "matched": matched,
        "missed": [kw for kw in keywords if kw.lower() not in answer_lower]
    }

# --- EVAL ---
def run_eval(prompt_version: str = "v1", model: str = "gpt-4o-mini", notes: str = ""):
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("footy_intel_eval")

    with mlflow.start_run():
        # log what changed
        mlflow.log_param("prompt_version", prompt_version)
        mlflow.log_param("model", model)
        mlflow.log_param("notes", notes)
        mlflow.log_param("test_cases", len(test_cases))

        results = []
        tool_correct = 0
        keyword_scores = []

        print(f"\nRunning eval — prompt: {prompt_version} | model: {model}\n")

        for tc in test_cases:
            print(f"[{tc['id']}] {tc['question'][:60]}...")

            try:
                start = time.time()
                result = run_agent(tc["question"])
                latency = round(time.time() - start, 3)

                tool_match = result["tool_used"] == tc["expected_tool"]
                keyword_result = score_answer(tc["question"], result["answer"], tc["keywords"])

                if tool_match:
                    tool_correct += 1
                keyword_scores.append(keyword_result["keyword_score"])

                entry = {
                    "id": tc["id"],
                    "question": tc["question"],
                    "expected_tool": tc["expected_tool"],
                    "actual_tool": result["tool_used"],
                    "tool_correct": tool_match,
                    "answer_preview": result["answer"][:150],
                    "keyword_score": keyword_result["keyword_score"],
                    "matched_keywords": keyword_result.get("matched", []),
                    "missed_keywords": keyword_result.get("missed", []),
                    "latency_seconds": latency,
                    "tokens": result["tokens"]
                }
                results.append(entry)

                status = "✅" if tool_match else "❌"
                print(f"  tool: {status} | keywords: {keyword_result['keyword_score']} | latency: {latency}s\n")

            except Exception as e:
                print(f"  ERROR: {str(e)}\n")
                results.append({"id": tc["id"], "error": str(e)})

        # --- SUMMARY ---
        tool_accuracy = round(tool_correct / len(test_cases), 2)
        avg_keyword_score = round(sum(keyword_scores) / len(keyword_scores), 2)
        avg_latency = round(sum(r.get("latency_seconds", 0) for r in results) / len(results), 3)
        avg_tokens = round(sum(r.get("tokens", 0) for r in results) / len(results))

        # log metrics to mlflow
        mlflow.log_metric("tool_accuracy", tool_accuracy)
        mlflow.log_metric("avg_keyword_score", avg_keyword_score)
        mlflow.log_metric("avg_latency_seconds", avg_latency)
        mlflow.log_metric("avg_tokens_per_query", avg_tokens)

        # save detailed results as artifact
        with open("eval_results.json", "w") as f:
            json.dump({"summary": {
                "prompt_version": prompt_version,
                "model": model,
                "tool_accuracy": tool_accuracy,
                "avg_keyword_score": avg_keyword_score,
                "avg_latency_seconds": avg_latency,
                "avg_tokens_per_query": avg_tokens
            }, "results": results}, f, indent=2)

        mlflow.log_artifact("eval_results.json")

        print("=" * 50)
        print("EVAL SUMMARY")
        print("=" * 50)
        print(f"  prompt_version:      {prompt_version}")
        print(f"  model:               {model}")
        print(f"  tool_accuracy:       {tool_accuracy}")
        print(f"  avg_keyword_score:   {avg_keyword_score}")
        print(f"  avg_latency_seconds: {avg_latency}")
        print(f"  avg_tokens:          {avg_tokens}")
        print("\nLogged to MLflow.")

if __name__ == "__main__":
    run_eval(prompt_version="v1", model="gpt-4o-mini", notes="baseline run")