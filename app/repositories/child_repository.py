from sqlalchemy.orm import Session
from app.models import Child
from app.repositories.base import BaseRepository

class ChildRepository(BaseRepository[Child]):
    """Репозиторий для работы с детьми"""
    
    def __init__(self, db: Session):
        super().__init__(Child, db)
    
    def get_by_group(self, group_id: int):
        return self.db.query(Child).filter(Child.group_id == group_id).all()
    
    def get_active(self):
        return self.db.query(Child).filter(Child.is_active == True).all()
    
    def get_with_discount(self):
        return self.db.query(Child).filter(Child.has_discount == True).all()