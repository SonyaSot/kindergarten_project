
# Эндпоинты для просмотра журнала действий


from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date

from app.database import get_db
from app.models import User, AuditLog
from app.routers.auth import get_current_user_from_token

router = APIRouter(prefix="/audit", tags=["Журнал действий"])

@router.get("/logs", response_model=List[dict])
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000, description="Количество записей"),
    user_id: Optional[int] = Query(None, description="Фильтр по пользователю"),
    action: Optional[str] = Query(None, description="Фильтр по действию"),
    resource: Optional[str] = Query(None, description="Фильтр по ресурсу"),
    start_date: Optional[date] = Query(None, description="Начальная дата"),
    end_date: Optional[date] = Query(None, description="Конечная дата"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    
    # Проверка прав доступа
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут просматривать журнал аудита"
        )
    
    # Формируем запрос
    query = db.query(AuditLog)
    
    # Применяем фильтры
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action.upper())
    if resource:
        query = query.filter(AuditLog.resource == resource.lower())
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    # Сортируем по дате (новые сначала) и ограничиваем
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    # Конвертируем в словари
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_email": log.user.email if log.user else None,
            "action": log.action,
            "resource": log.resource,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at
        }
        for log in logs
    ]

@router.get("/stats")
async def get_audit_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
   
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы"
        )
    
    # Общая статистика
    total_logs = db.query(AuditLog).count()
    
    # По действиям
    actions_count = db.query(
        AuditLog.action, 
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).all()
    
    # По ресурсам
    resources_count = db.query(
        AuditLog.resource, 
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.resource).all()
    
    return {
        "total_logs": total_logs,
        "by_action": {action: count for action, count in actions_count},
        "by_resource": {resource: count for resource, count in resources_count}
    }