from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.project import Project, ResourceAllocation
from models.employee import Employee
from models.timesheet import Timesheet

class PredictionEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def predict_project_delays(self) -> List[Dict[str, Any]]:
        """
        Predict project delay probability based on planned vs actual hours and allocations.
        """
        stmt = select(Project).where(Project.status == "Active")
        result = await self.db.execute(stmt)
        projects = result.scalars().all()

        predictions = []
        for p in projects:
            # Dummy prediction logic
            delay_prob = 0.1
            if p.budget and p.planned_hours:
                # E.g. risk increases if planned_hours > budget threshold
                delay_prob += 0.2
            
            predictions.append({
                "project_id": p.project_id,
                "project_name": p.project_name,
                "delay_probability": delay_prob,
                "risk_level": "High" if delay_prob > 0.5 else "Low",
                "recommended_intervention": "Increase resource allocation" if delay_prob > 0.5 else "None"
            })
        return predictions

    async def predict_resource_shortages(self) -> List[Dict[str, Any]]:
        """
        Predict resource shortages based on current allocations and upcoming projects.
        """
        # Dummy prediction logic
        return [
            {
                "skill": "Python Developer",
                "shortage_probability": 0.8,
                "predicted_deficit": 3,
                "recommendation": "Initiate hiring for 3 Senior Python Developers"
            }
        ]

    async def predict_utilization_trends(self) -> Dict[str, Any]:
        """
        Predict utilization trends over the next quarter.
        """
        return {
            "current_utilization": 82.5,
            "predicted_next_month": 85.0,
            "predicted_next_quarter": 88.5,
            "bench_size_prediction": 5
        }
