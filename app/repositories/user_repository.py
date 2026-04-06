from sqlalchemy.orm import Session
from app.models import User
from app.repositories.base import BaseRepository

#Репозиторий для работы с пользователями
class UserRepository(BaseRepository[User]):
        
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_role(self, role: str):
        return self.db.query(User).filter(User.role == role).all()