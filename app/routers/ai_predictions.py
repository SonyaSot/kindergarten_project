from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.models import User, Group
from app.routers.auth import get_current_user_from_token
from app.ai_module.xgb_service import XGBPredictor

router = APIRouter(prefix="/ai", tags=["AI Прогнозы"])

@router.get("/predictions/group/{group_id}")
async def predict_group_attendance(
    group_id: int = Path(..., description="ID группы"),
    target_date: Optional[date] = Query(None, description="Дата прогноза"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
#Прогноз посещаемости на основе XGBoost
    if target_date is None:
        target_date = date.today() + timedelta(days=1)
    
    predictor = XGBPredictor(db)
    return predictor.predict_group(group_id, target_date)

@router.post("/train")
async def train_model_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    
#Переобучить модель ИИ. Доступно только администраторам.
    
    if current_user.role != "admin":
        raise HTTPException(403, "Только администраторы могут обучать модель")
    
    predictor = XGBPredictor(db)
    success = predictor.train_model()
    
    if success:
        return {"message": "Модель успешно переобучена"}
    else:
        raise HTTPException(500, "Недостаточно данных для обучения")