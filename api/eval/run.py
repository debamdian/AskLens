"""Evaluation Benchmark Runner for AskLens.

Usage:
    cd api && python -m eval.run
    cd api && python -m eval.run --live   # includes PostgreSQL execution accuracy
"""

import argparse
import time
from pathlib import Path
from typing import Any, Dict, List
import yaml

from app.agents.router import IntentRouter, intent_router
from app.sql.validator import SQLValidator, SQLValidationError
from app.db.connector import warehouse_connector


EVAL_SET_PATH = Path(__file__).resolve().parent / "eval_set.yaml"


class _OfflineLLM:
    """Stub LLM used in --offline mode to test heuristic routing + SQL safety without network calls."""

    def generate(self, *args, **kwargs):
        raise RuntimeError("Offline mode")


def load_eval_cases(path: Path = EVAL_SET_PATH) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("cases", [])


def run_evaluation(live_db: bool = False, offline: bool = False) -> Dict[str, Any]:
    cases = load_eval_cases()
    validator = SQLValidator(dialect="postgres", max_limit=500)
    router = IntentRouter(llm=_OfflineLLM()) if offline else intent_router

    total = len(cases)
    intent_correct = 0
    sql_safety_passed = 0
    sql_safety_total = 0
    db_exec_passed = 0
    db_exec_total = 0
    latencies_ms: List[float] = []
    failures: List[Dict[str, str]] = []

    db_available = live_db and warehouse_connector.test_connection()
    if live_db and not db_available:
        print("[WARN] PostgreSQL not reachable; running offline routing + SQL safety evaluation.")

    for case in cases:
        qid = case["id"]
        question = case["question"]
        expected_intent = case["expected_intent"]
        ref_sql = case.get("reference_sql")
        should_block = bool(case.get("should_block", False))

        t0 = time.perf_counter()
        decision = router.route(question)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)

        if decision.intent == expected_intent:
            intent_correct += 1
        else:
            failures.append({
                "id": qid,
                "stage": "intent_router",
                "detail": f"Expected '{expected_intent}', got '{decision.intent}' for: {question}",
            })

        if ref_sql:
            sql_safety_total += 1
            if should_block:
                try:
                    validator.validate_and_sanitize(ref_sql)
                    failures.append({
                        "id": qid,
                        "stage": "sql_safety",
                        "detail": f"Expected unsafe SQL to be blocked, but passed: {ref_sql}",
                    })
                except SQLValidationError:
                    sql_safety_passed += 1
            else:
                try:
                    sanitized = validator.validate_and_sanitize(ref_sql)
                    sql_safety_passed += 1
                    if db_available:
                        db_exec_total += 1
                        res = warehouse_connector.execute_read_only(sanitized)
                        if res.row_count >= 0:
                            db_exec_passed += 1
                except Exception as exc:
                    failures.append({
                        "id": qid,
                        "stage": "sql_safety_or_exec",
                        "detail": f"Valid SQL failed ({exc}): {ref_sql}",
                    })

    avg_latency = sum(latencies_ms) / len(latencies_ms) if latencies_ms else 0.0
    intent_acc = (intent_correct / total * 100.0) if total else 0.0
    safety_acc = (sql_safety_passed / sql_safety_total * 100.0) if sql_safety_total else 0.0
    exec_acc = (db_exec_passed / db_exec_total * 100.0) if db_exec_total else None

    print("\n=== AskLens Evaluation Report ===")
    print(f"Total Cases        : {total}")
    print(f"Intent Accuracy    : {intent_correct}/{total} ({intent_acc:.1f}%)")
    print(f"SQL Safety Accuracy: {sql_safety_passed}/{sql_safety_total} ({safety_acc:.1f}%)")
    if exec_acc is not None:
        print(f"DB Execution Acc   : {db_exec_passed}/{db_exec_total} ({exec_acc:.1f}%)")
    print(f"Avg Router Latency : {avg_latency:.2f} ms")
    print(f"Failures           : {len(failures)}")
    for f in failures[:10]:
        print(f"  - [{f['id']}] ({f['stage']}) {f['detail']}")

    return {
        "total": total,
        "intent_accuracy": intent_acc,
        "sql_safety_accuracy": safety_acc,
        "execution_accuracy": exec_acc,
        "avg_latency_ms": avg_latency,
        "failures": failures,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AskLens evaluation benchmark.")
    parser.add_argument("--live", action="store_true", help="Also run SQL execution against PostgreSQL.")
    parser.add_argument("--offline", action="store_true", help="Run heuristic router + SQL safety offline without LLM calls.")
    args = parser.parse_args()
    report = run_evaluation(live_db=args.live, offline=args.offline)
    raise SystemExit(1 if report["failures"] else 0)
