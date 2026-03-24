from sqlalchemy.orm import Session
from app.repositories.child_repository import ChildRepository
from app.models import Child
from app.schemas.child import ChildCreate

class ChildService:
    """Сервис для работы с детьми - паттерн Service Layer"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ChildRepository(db)
    
    def create_child(self, child_data: ChildCreate) -> Child:
        """Бизнес-логика создания ребенка"""
        # Валидация
        if not child_data.full_name:
            raise ValueError("Имя ребенка обязательно")
        
        if not child_data.date_of_birth:
            raise ValueError("Дата рождения обязательна")
        
        # Создание через репозиторий
        return self.repository.create({
            "full_name": child_data.full_name,
            "date_of_birth": child_data.date_of_birth,
            "group_id": child_data.group_id,
            "parent_name": child_data.parent_name,
            "parent_phone": child_data.parent_phone,
            "parent_email": child_data.parent_email,
            "has_discount": child_data.has_discount,
            "discount_reason": child_data.discount_reason,
            "is_active": True
        })
    
    def get_children_by_group(self, group_id: int):
        """Бизнес-логика: получить детей группы"""
        return self.repository.get_by_group(group_id)
    
    def get_discount_children(self):
        """Бизнес-логика: получить детей со скидкой"""
        return self.repository.get_with_discount()