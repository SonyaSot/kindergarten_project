from sqlalchemy.orm import Session
from app.repositories.child_repository import ChildRepository
from app.models import Child
from app.schemas.child import ChildCreate

# Сервис для работы с детьми - паттерн Service Layer
class ChildService:
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ChildRepository(db)
    
    # Бизнес-логика создания ребенка
    def create_child(self, child_data: ChildCreate) -> Child:   
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

    #  Получить всех детей (для админа)
    def get_all_children(self):
        """Получить всех детей из всех групп"""
        return self.repository.get_all()
    
    # Бизнес-логика: получить детей группы    
    def get_children_by_group(self, group_id: int):
        """Получить детей конкретной группы"""
        return self.repository.get_by_group(group_id)
    
    # Бизнес-логика: получить детей со скидкой
    def get_discount_children(self):
        """Получить детей со скидкой"""
        return self.repository.get_with_discount()