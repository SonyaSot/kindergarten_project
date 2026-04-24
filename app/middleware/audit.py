from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.database import get_db
from app.models import AuditLog, User


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Сначала выполняем запрос
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as app_exc:
            # Если ошибка в эндпоинте — всё равно логируем!
            status_code = 500
            response = None  # Продолжаем логировать
            raise app_exc  # Пробрасываем ошибку дальше
        finally:
            # Логируем ВСЕГДА (даже при ошибке)
            if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                try:
                    db = next(get_db())
                    
                    user_id = None
                    auth_header = request.headers.get("Authorization")
                    
                    if auth_header and auth_header.startswith("Bearer "):
                        token = auth_header.replace("Bearer ", "")
                        try:
                            secret_key = os.getenv("SECRET_KEY", "dev-key")
                            from jose import jwt
                            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
                            sub = payload.get("sub")
                            if sub and "@" in str(sub):
                                user = db.query(User).filter(User.email == sub).first()
                                if user:
                                    user_id = user.id
                            elif sub and str(sub).isdigit():
                                user_id = int(sub)
                        except:
                            pass  # Если токен не декодировался — логируем с user_id=None
                    
                    path_parts = request.url.path.strip("/").split("/")
                    resource = path_parts[0] if path_parts and path_parts[0] else "unknown"
                    
                    resource_id = None
                    for part in path_parts:
                        if part.isdigit():
                            resource_id = int(part)
                            break
                    
                    action_map = {"POST": "CREATE", "PUT": "UPDATE", "PATCH": "UPDATE", "DELETE": "DELETE"}
                    action = action_map.get(request.method, request.method)
                    
                    audit_log = AuditLog(
                        user_id=user_id,
                        action=action,
                        resource=resource,
                        resource_id=resource_id,
                        details=f"{request.method} {request.url.path} (status:{status_code})",
                        ip_address=request.client.host if request.client else None,
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(audit_log)
                    db.commit()
                    
                except Exception as e:
                    print(f"⚠️ Audit log error: {e}")
                finally:
                    try:
                        db.close()
                    except:
                        pass
        
        return response