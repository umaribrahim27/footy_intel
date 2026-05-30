import json
import time
from graph import run_agent

# --- TEST SET ---
# Each test has:
# - question: what we ask
# - expected_tool: what tool the agent should use
# - keywords: words that should appear in a good answer
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

def run_eval():
    results = []
    tool_correct = 0
    keyword_scores = []

    print(f"\nRunning eval on {len(test_cases)} test cases...\n")

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
            print(f"  tool: {status} (expected {tc['expected_tool']}, got {result['tool_used']})")
            print(f"  keywords: {keyword_result['keyword_score']} | latency: {latency}s\n")

        except Exception as e:
            print(f"  ERROR: {str(e)}\n")
            results.append({"id": tc["id"], "error": str(e)})

    # --- SUMMARY ---
    tool_accuracy = round(tool_correct / len(test_cases), 2)
    avg_keyword_score = round(sum(keyword_scores) / len(keyword_scores), 2)
    avg_latency = round(sum(r.get("latency_seconds", 0) for r in results) / len(results), 3)
    avg_tokens = round(sum(r.get("tokens", 0) for r in results) / len(results))

    summary = {
        "total_cases": len(test_cases),
        "tool_accuracy": tool_accuracy,
        "avg_keyword_score": avg_keyword_score,
        "avg_latency_seconds": avg_latency,
        "avg_tokens_per_query": avg_tokens,
        "tool_correct": tool_correct,
        "tool_incorrect": len(test_cases) - tool_correct
    }

    print("=" * 50)
    print("EVAL SUMMARY")
    print("=" * 50)
    for k, v in summary.items():
        print(f"  {k}: {v}")

    # save results
    with open("eval_results.json", "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    print("\nFull results saved to eval_results.json")
    return summary

if __name__ == "__main__":
    run_eval()