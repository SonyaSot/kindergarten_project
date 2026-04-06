from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random

# Подключение к БД
engine = create_engine('postgresql://postgres:postgres123@db:5432/kindergarten_db')
Session = sessionmaker(bind=engine)
session = Session()

# Получаем всех детей с teacher_id их группы
result = session.execute(text("""
    SELECT c.id as child_id, g.teacher_id 
    FROM children c 
    JOIN groups g ON c.group_id = g.id
"""))
children_data = [(row[0], row[1]) for row in result]  # (child_id, teacher_id)

print(f"Найдено детей: {len(children_data)}")

if len(children_data) == 0:
    print("Нет детей в базе!")
    exit(1)

# СТАТУСЫ В ВЕРХНЕМ РЕГИСТРЕ (ENUM)
statuses = ['PRESENT'] * 16 + ['SICK'] * 3 + ['ABSENT']

# Генерируем 100 записей
for i in range(100):
    child_id, teacher_id = random.choice(children_data)
    days_ago = random.randint(1, 90)
    date = datetime.now() - timedelta(days=days_ago)
    status = random.choice(statuses)
    
    # ВСТАВЛЯЕМ ТОЛЬКО СУЩЕСТВУЮЩИЕ КОЛОНКИ:
    session.execute(
        text("""
            INSERT INTO attendance 
            (child_id, teacher_id, date, status) 
            VALUES (:child_id, :teacher_id, :date, :status)
        """),
        {
            "child_id": child_id, 
            "teacher_id": teacher_id,
            "date": date, 
            "status": status
        }
    )

session.commit()
print("Создано 100 записей о посещаемости!")
print("Теперь переобучи модель: POST /ai/train")