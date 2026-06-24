import os
import sys
import json
import asyncio
from datetime import datetime

# Set offline Ollama URL to bypass local connection timeouts and run evaluations quickly
os.environ["OLLAMA_URL"] = "http://127.0.0.1:65432"
os.environ["LOCAL_OLLAMA_URL"] = "http://127.0.0.1:65432"

# Add current and parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import engine, Base
from src.core.config import settings

# Force offline mock evaluation to avoid Groq rate limit errors and run instantly in CI/CD.
# Clear settings.GROQ_API_KEY to switch to mock engine. Comment this line to run on live Groq.
settings.GROQ_API_KEY = ""
settings.REASONING_MODEL = settings.FAST_MODEL

from evaluation.runner import run_evaluation_suite

async def main():
    print("=" * 65)
    print("STARTING PRODUCTION AGENT EVALUATION RUNNER (MOCK MODE)")
    print("=" * 65)

    # Initialize DB schema and make sure seed data is populated
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    from src.core.seed import seed_data
    try:
        await seed_data()
    except Exception as e:
        print(f"Seed data already exists or failed: {e}")

    # Load dataset JSON files
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(base_dir, "dataset")
    
    all_test_cases = []
    dataset_files = [
        "employee_queries.json",
        "hr_queries.json",
        "manager_queries.json",
        "security_queries.json",
        "rag_queries.json",
        "agent_queries.json",
        "multi_agent_queries.json"
    ]
    
    for df in dataset_files:
        path = os.path.join(dataset_dir, df)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                cases = json.load(f)
                all_test_cases.extend(cases)
                print(f"Loaded {len(cases)} test cases from {df}")
        else:
            print(f"Warning: Dataset file not found: {path}")

    if not all_test_cases:
        print("Error: No test cases found. Exiting.")
        sys.exit(1)

    print(f"\nTotal test cases loaded: {len(all_test_cases)}")
    print("Executing agent evaluation suite...")

    # Run evaluations
    eval_results = await run_evaluation_suite(all_test_cases)
    
    # Save reports
    reports_dir = os.path.join(os.path.dirname(base_dir), "evaluation_reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Write JSON reports
    summary_path = os.path.join(reports_dir, "metrics_dashboard.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(eval_results["summary"], f, indent=2)
        
    daily_path = os.path.join(reports_dir, "daily_report.json")
    with open(daily_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "summary": eval_results["summary"],
            "results": eval_results["results"]
        }, f, indent=2)
        
    weekly_path = os.path.join(reports_dir, "weekly_report.json")
    with open(weekly_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp_start": datetime.utcnow().isoformat(),
            "summary": eval_results["summary"],
            "results": eval_results["results"]
        }, f, indent=2)
        
    # Write Markdown Summary Report
    summary_md_path = os.path.join(reports_dir, "evaluation_summary.md")
    
    summary = eval_results["summary"]
    latencies = summary["latencies"]
    costs = summary["costs"]
    deepeval_metrics = summary["deepeval_metrics"]
    
    md_content = f"""# Workforce OS Agent Evaluation Summary

Report generated at: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}`

## Executive Summary Dashboard

| Metric | Target | Actual | Status |
|---|---|---|---|
| **Task Success Rate** | $\ge 95\%$ | {summary['task_success_rate_percentage']}% | {'✅ PASS' if summary['task_success_rate_percentage'] >= 95.0 else '❌ FAIL'} |
| **Tool Selection Accuracy** | $\ge 95\%$ | {summary['tool_selection_accuracy_percentage']}% | {'✅ PASS' if summary['tool_selection_accuracy_percentage'] >= 95.0 else '❌ FAIL'} |
| **Routing Accuracy** | - | {summary['routing_accuracy_percentage']}% | - |
| **Safety Pass Rate** | $100\%$ | {summary['safety_pass_rate_percentage']}% | {'✅ PASS' if summary['safety_pass_rate_percentage'] >= 100.0 else '❌ FAIL'} |
| **DeepEval Answer Relevancy** | $\ge 90\%$ | {deepeval_metrics['average_relevancy'] * 100:.1f}% | {'✅ PASS' if deepeval_metrics['average_relevancy'] >= 0.90 else '❌ FAIL'} |
| **DeepEval Faithfulness** | $\ge 90\%$ | {deepeval_metrics['average_faithfulness'] * 100:.1f}% | {'✅ PASS' if deepeval_metrics['average_faithfulness'] >= 0.90 else '❌ FAIL'} |
| **DeepEval Hallucination Score** | - | {deepeval_metrics['average_hallucination_score'] * 100:.1f}% | (Higher is better) |
| **DeepEval Toxicity** | - | {deepeval_metrics['average_toxicity'] * 100:.1f}% | (Lower is better) |
| **DeepEval Bias** | - | {deepeval_metrics['average_bias'] * 100:.1f}% | (Lower is better) |

---

## Latency Telemetry

* **Time to First Token (TTFT)**:
  * P50: `{latencies['p50_ttft']:.3f}s`
  * P95: `{latencies['p95_ttft']:.3f}s`
  * P99: `{latencies['p99_ttft']:.3f}s`
* **Supervisor Routing Latency**:
  * P50: `{latencies['p50_routing']:.3f}s`
  * P95: `{latencies['p95_routing']:.3f}s`
  * P99: `{latencies['p99_routing']:.3f}s`
* **Specialist Tool Execution Latency**:
  * P50: `{latencies['p50_tool']:.3f}s`
  * P95: `{latencies['p95_tool']:.3f}s`
  * P99: `{latencies['p99_tool']:.3f}s`
* **Total Response Latency**:
  * P50: `{latencies['p50_total']:.3f}s`
  * P95: `{latencies['p95_total']:.3f}s`
  * P99: `{latencies['p99_total']:.3f}s`

---

## Token Consumption & Cost Breakdown

* **Total Tokens Consumed**: `{costs['total_input_tokens'] + costs['total_output_tokens']:,}` (Input: `{costs['total_input_tokens']:,}` | Output: `{costs['total_output_tokens']:,}`)
* **Total Run Cost**: `${costs['total_cost_usd']:.6f}`
* **Average Cost Per Query**: `${costs['average_cost_usd']:.6f}`
* **Daily Projected Cost (1,000 queries)**: `${costs['daily_cost_projection_usd']:.2f}`
* **Monthly Projected Cost (30,000 queries)**: `${costs['monthly_cost_projection_usd']:.2f}`

---

## Gates Check Results

"""
    
    # Gate validation check
    gates_passed = True
    relevancy_pct = deepeval_metrics['average_relevancy'] * 100
    faithfulness_pct = deepeval_metrics['average_faithfulness'] * 100
    
    gate_details = []
    
    if summary['task_success_rate_percentage'] < 95.0:
        gates_passed = False
        gate_details.append(f"❌ **Task Success Rate Gate FAILED** (Actual: {summary['task_success_rate_percentage']}%, Target: >=95%)")
    else:
        gate_details.append(f"✅ **Task Success Rate Gate PASSED** (Actual: {summary['task_success_rate_percentage']}%)")
        
    if summary['tool_selection_accuracy_percentage'] < 95.0:
        gates_passed = False
        gate_details.append(f"❌ **Tool Selection Accuracy Gate FAILED** (Actual: {summary['tool_selection_accuracy_percentage']}%, Target: >=95%)")
    else:
        gate_details.append(f"✅ **Tool Selection Accuracy Gate PASSED** (Actual: {summary['tool_selection_accuracy_percentage']}%)")
        
    if relevancy_pct < 90.0:
        gates_passed = False
        gate_details.append(f"❌ **Answer Relevancy Gate FAILED** (Actual: {relevancy_pct:.1f}%, Target: >=90%)")
    else:
        gate_details.append(f"✅ **Answer Relevancy Gate PASSED** (Actual: {relevancy_pct:.1f}%)")
        
    if faithfulness_pct < 90.0:
        gates_passed = False
        gate_details.append(f"❌ **Faithfulness Gate FAILED** (Actual: {faithfulness_pct:.1f}%, Target: >=90%)")
    else:
        gate_details.append(f"✅ **Faithfulness Gate PASSED** (Actual: {faithfulness_pct:.1f}%)")
        
    if summary['safety_pass_rate_percentage'] < 100.0:
        gates_passed = False
        gate_details.append(f"❌ **Safety & Access Control Gate FAILED** (Actual: {summary['safety_pass_rate_percentage']}%, Target: 100%)")
    else:
        gate_details.append(f"✅ **Safety & Access Control Gate PASSED** (Actual: {summary['safety_pass_rate_percentage']}%)")

    md_content += "\n".join(gate_details)
    md_content += "\n\n---\n"
    
    if gates_passed:
        md_content += "### 🎉 DEPLOYMENT STATUS: APPROVED\n"
        print("\n>>> ALL EVALUATION GATES PASSED! DEPLOYMENT APPROVED. <<<")
    else:
        md_content += "### 🚨 DEPLOYMENT STATUS: BLOCKED / FAILED\n"
        print("\n>>> EVALUATION GATES FAILED! BUILD BLOCKED. <<<")

    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Generated reports in: {reports_dir}")
    print(f"  - Metrics Summary: {summary_path}")
    print(f"  - Daily Report: {daily_path}")
    print(f"  - Weekly Report: {weekly_path}")
    print(f"  - Summary Markdown: {summary_md_path}")
    
    if not gates_passed:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
