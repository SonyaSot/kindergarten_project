from sqlalchemy.orm import Session
from app.models import Group
from app.repositories.base import BaseRepository

class GroupRepository(BaseRepository[Group]):
    """Репозиторий для работы с группами"""
    
    def __init__(self, db: Session):
        super().__init__(Group, db)
    
    def get_by_teacher(self, teacher_id: int):
        return self.db.query(Group).filter(Group.teacher_id == teacher_id).all()