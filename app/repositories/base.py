from sqlalchemy.orm import Session
from typing import Generic, TypeVar, Type, Optional, List

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """Базовый репозиторий - паттерн Repository"""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: int) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self) -> List[ModelType]:
        return self.db.query(self.model).all()
    
    def create(self, obj_in: dict) -> ModelType:
        obj_in_db = self.model(**obj_in)
        self.db.add(obj_in_db)
        self.db.commit()
        self.db.refresh(obj_in_db)
        return obj_in_db
    
    def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        obj_in_db = self.get(id)
        if obj_in_db:
            for field, value in obj_in.items():
                setattr(obj_in_db, field, value)
            self.db.commit()
            self.db.refresh(obj_in_db)
        return obj_in_db
    
    def delete(self, id: int) -> bool:
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False