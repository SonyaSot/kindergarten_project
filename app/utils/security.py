from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# === НАСТРОЙКИ БЕЗОПАСНОСТИ ===
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

# === ХЭШИРОВАНИЕ ПАРОЛЕЙ ===
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить, совпадает ли пароль с хэшем"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Получить хэш пароля"""
    return pwd_context.hash(password)

# === РАБОТА С JWT ТОКЕНАМИ ===
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создать JWT токен доступа"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt