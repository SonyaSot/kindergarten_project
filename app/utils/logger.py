"""
app/utils/logger.py - Утилита для логирования действий пользователей
"""

from sqlalchemy.orm import Session
from app.models import AuditLog
from typing import Optional

def log_action(
    db: Session,
    user_id: int,
    action: str,
    resource: str,
    resource_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """
    Записать действие пользователя в журнал аудита.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        action: Тип действия (CREATE, UPDATE, DELETE, LOGIN)
        resource: Ресурс (children, groups, payments)
        resource_id: ID затронутого объекта
        details: Дополнительные данные
        ip_address: IP адрес клиента
    """
    try:
        log_entry = AuditLog(
            user_id=user_id,
            action=action.upper(),  # Приводим к верхнему регистру
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        # Если логирование не сработало - не ломаем основное приложение
        db.rollback()
        print(f"Audit log error: {e}")