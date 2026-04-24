"""
app/utils/audit.py
Функция для логирования действий
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional  # ← ✅ ДОБАВЬ ЭТУ СТРОКУ!

from app.models import AuditLog


def log_action(
    db: Session,
    user_id: int,
    action: str,
    resource: str,
    resource_id: Optional[int] = None,  # Теперь Optional известен
    details: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Записать действие в аудит"""
    try:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"⚠️ Audit log error: {e}")