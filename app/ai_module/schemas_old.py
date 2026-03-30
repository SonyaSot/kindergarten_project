from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional, Dict

class AttendancePrediction(BaseModel):
    child_id: int
    child_name: str
    predicted_days: int
    confidence: float
    risk_level: str  # "low", "medium", "high"
    patterns: Dict[str, float]

class BudgetPrediction(BaseModel):
    month: date
    total_predicted_revenue: float
    total_children: int
    average_attendance: float
    confidence: float
    breakdown: List[AttendancePrediction]

class RiskAlert(BaseModel):
    child_id: int
    child_name: str
    risk_type: str  # "frequent_absence", "illness_pattern", "payment_issue"
    risk_score: float
    recommendation: str
    historical_data: Dict  

class AIPredictionResponse(BaseModel):
    predictions: List[AttendancePrediction]
    budget_forecast: BudgetPrediction
    risk_alerts: List[RiskAlert]
    generated_at: date
    model_version: str