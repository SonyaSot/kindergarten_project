from sqlalchemy.orm import Session
from app.models import Child

class ChildRepository:
    
    def __init__(self, db: Session):
        self.db = db
    
    #  Получить всех детей
    def get_all(self):
        """Получить всех детей из базы"""
        return self.db.query(Child).all()
    
    # Существующий метод: Получить детей группы
    def get_by_group(self, group_id: int):
        """Получить детей конкретной группы"""
        return self.db.query(Child).filter(Child.group_id == group_id).all()
    
    # Существующий метод: Получить детей со скидкой
    def get_with_discount(self):
        """Получить детей со скидкой"""
        return self.db.query(Child).filter(Child.has_discount == True).all()
    
    # Существующий метод: Создать ребенка
    def create(self, child_data: dict):
        """Создать нового ребенка"""
        child = Child(**child_data)
        self.db.add(child)
        self.db.commit()
        self.db.refresh(child)
        return child