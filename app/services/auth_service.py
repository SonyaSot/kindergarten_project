from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.utils.security import verify_password, get_password_hash
from app.models import User
from typing import Optional  

#Сервис для аутентификации - паттерн Service Layer
class AuthService:
      
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)
    
    #Бизнес-логика аутентификации
    def authenticate(self, email: str, password: str) -> User | None:
        user = self.repository.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    #Бизнес-логика создания пользователя
    def create_user(self, email: str, password: str, full_name: str, role: str) -> User: 
        hashed_password = get_password_hash(password)
        return self.repository.create({
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
            "role": role,
            "is_active": True
        })