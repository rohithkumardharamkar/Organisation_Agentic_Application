import os
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List

from src.core.database import get_db, SessionLocal
from src.models.db_models import EvaluationRun, EvaluationCaseResult
from evaluation.runner import run_evaluation_suite
from src.core.config import settings

router = APIRouter(prefix="/evaluations", tags=["Agent Evaluations"])

async def background_run_evaluation(run_id: int):
    # Initialize session
    async with SessionLocal() as db:
        # Load dataset JSON files
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dataset_dir = os.path.join(base_dir, "evaluation", "dataset")
        
        all_test_cases = []
        dataset_files = [
            "employee_queries.json",
            "hr_queries.json",
            "manager_queries.json",
            "security_queries.json",
            "rag_queries.json",
            "agent_queries.json"
        ]
        
        for df in dataset_files:
            path = os.path.join(dataset_dir, df)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        cases = json.load(f)
                        all_test_cases.extend(cases)
                except Exception as e:
                    print(f"Error reading {path}: {e}")
                    
        if not all_test_cases:
            print("No test cases found for evaluation background run.")
            return
            
        # Run evaluations
        try:
            eval_results = await run_evaluation_suite(all_test_cases)
            
            summary = eval_results["summary"]
            cases_res = eval_results["results"]
            
            # Update the EvaluationRun row in the DB
            stmt = select(EvaluationRun).where(EvaluationRun.id == run_id)
            res = await db.execute(stmt)
            run_row = res.scalar_one_or_none()
            
            if run_row:
                run_row.total_cases = len(cases_res)
                run_row.routing_accuracy = summary.get("routing_accuracy_percentage", 0.0) / 100.0
                run_row.tool_selection_accuracy = summary.get("tool_selection_accuracy_percentage", 0.0) / 100.0
                
                deepeval_metrics = summary.get("deepeval_metrics", {})
                run_row.hallucination_rate = max(0.0, 1.0 - deepeval_metrics.get("average_hallucination_score", 1.0))
                
                # RAG metrics
                run_row.rag_precision = deepeval_metrics.get("average_relevancy", 0.0)
                run_row.rag_recall = deepeval_metrics.get("average_faithfulness", 0.0)
                
                run_row.agent_success_rate = summary.get("task_success_rate_percentage", 0.0) / 100.0
                run_row.workflow_completion_rate = summary.get("safety_pass_rate_percentage", 0.0) / 100.0
                run_row.user_satisfaction_score = deepeval_metrics.get("average_relevancy", 0.0) * 5.0 # normalized to 5 stars
                
                db.add(run_row)
                
            # Write EvaluationCaseResult rows
            for c in cases_res:
                actual_tool = c.get("actual_tool")
                expected_tool = c.get("expected_tool")
                
                case_row = EvaluationCaseResult(
                    run_id=run_id,
                    query=c.get("query", ""),
                    role=c.get("role", "Employee"),
                    expected_agent=c.get("expected_agent"),
                    actual_agent=c.get("actual_agent"),
                    routing_correct=c.get("routing_correct", False),
                    tool_selected=actual_tool,
                    tool_correct=c.get("tool_correct", False),
                    hallucination_detected=c.get("deepeval", {}).get("hallucination_score", 0.0) < 0.70,
                    rag_precision=c.get("deepeval", {}).get("relevancy_score", 0.0),
                    rag_recall=c.get("deepeval", {}).get("faithfulness_score", 0.0),
                    success=c.get("task_success", False),
                    feedback=c.get("deepeval", {}).get("relevancy_reason", "")
                )
                db.add(case_row)
                
            await db.commit()
            print(f"Evaluation Run {run_id} completed and database records saved successfully!")
            
        except Exception as e:
            print(f"Exception during background evaluation: {e}")
            await db.rollback()

@router.get("/runs")
async def get_evaluation_runs(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    stmt = select(EvaluationRun).order_by(EvaluationRun.timestamp.desc())
    res = await db.execute(stmt)
    runs = res.scalars().all()
    
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "total_cases": r.total_cases,
            "routing_accuracy": r.routing_accuracy,
            "tool_selection_accuracy": r.tool_selection_accuracy,
            "hallucination_rate": r.hallucination_rate,
            "rag_precision": r.rag_precision,
            "rag_recall": r.rag_recall,
            "agent_success_rate": r.agent_success_rate,
            "workflow_completion_rate": r.workflow_completion_rate,
            "user_satisfaction_score": r.user_satisfaction_score
        }
        for r in runs
    ]

@router.get("/runs/{run_id}/results")
async def get_evaluation_results(run_id: int, db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    stmt = select(EvaluationCaseResult).where(EvaluationCaseResult.run_id == run_id)
    res = await db.execute(stmt)
    results = res.scalars().all()
    
    return [
        {
            "id": c.id,
            "query": c.query,
            "role": c.role,
            "expected_agent": c.expected_agent,
            "actual_agent": c.actual_agent,
            "routing_correct": c.routing_correct,
            "tool_selected": c.tool_selected,
            "tool_correct": c.tool_correct,
            "hallucination_detected": c.hallucination_detected,
            "rag_precision": c.rag_precision,
            "rag_recall": c.rag_recall,
            "success": c.success,
            "feedback": c.feedback
        }
        for c in results
    ]

@router.post("/run")
async def trigger_evaluation_run(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    new_run = EvaluationRun(
        timestamp=datetime.utcnow(),
        total_cases=0,
        routing_accuracy=0.0,
        tool_selection_accuracy=0.0,
        hallucination_rate=0.0,
        rag_precision=0.0,
        rag_recall=0.0,
        agent_success_rate=0.0,
        workflow_completion_rate=0.0,
        user_satisfaction_score=0.0
    )
    db.add(new_run)
    await db.commit()
    await db.refresh(new_run)
    
    background_tasks.add_task(background_run_evaluation, run_id=new_run.id)
    
    return {
        "status": "success",
        "message": "Evaluation suite triggered successfully.",
        "run_id": new_run.id
    }
