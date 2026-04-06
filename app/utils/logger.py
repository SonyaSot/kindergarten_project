
#Утилита для логирования действий пользователей


from sqlalchemy.orm import Session
from app.models import AuditLog
from typing import Optional

def log_action(
    db: Session, #Сессия базы данных
    user_id: int, #ID пользователя
    action: str, #Тип действия (CREATE, UPDATE, DELETE, LOGIN)
    resource: str, #Ресурс (children, groups, payments)
    resource_id: Optional[int] = None, #ID затронутого объекта
    details: Optional[str] = None, #Дополнительные данные
    ip_address: Optional[str] = None #IP адрес клиента
):

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
        db.rollback()
        print(f"Audit log error: {e}")