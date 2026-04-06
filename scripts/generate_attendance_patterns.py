"""
Генерация данных о посещаемости с паттернами для обучения ИИ
ИСПРАВЛЕННАЯ ВЕРСИЯ: использует реальные child_id и teacher_id из БД
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random

# Подключение к БД
engine = create_engine('postgresql://postgres:postgres123@db:5432/kindergarten_db')
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 60)
print("ГЕНЕРАЦИЯ ДАННЫХ С ПАТТЕРНАМИ ДЛЯ ИИ")
print("=" * 60)

# ПОЛУЧАЕМ РЕАЛЬНЫЕ ID ИЗ БД
print("\nЗагружаю реальные данные из базы...")

# Дети
result = session.execute(text("SELECT id FROM children ORDER BY id"))
valid_child_ids = [row[0] for row in result]

# Учителя: берём ВСЕХ пользователей (без фильтра по роли!)
result = session.execute(text("SELECT id FROM users ORDER BY id"))
valid_teacher_ids = [row[0] for row in result]

print(f"Найдено детей: {len(valid_child_ids)}")
print(f"Найдено пользователей: {len(valid_teacher_ids)}")

if len(valid_child_ids) == 0:
    print("❌ Нет детей в базе!")
    exit(1)

if len(valid_teacher_ids) == 0:
    print("Нет пользователей в базе!")
    exit(1)

# 1. Генерируем данные ЗИМОЙ (январь-февраль) — больше болезней
print("\nГенерирую данные ЗИМОЙ (много болезней)...")
winter_statuses = ['SICK'] * 6 + ['ABSENT'] * 2 + ['PRESENT'] * 2

for i in range(80):
    child_id = random.choice(valid_child_ids)
    teacher_id = random.choice(valid_teacher_ids)
    days_offset = random.randint(0, 60)
    date = datetime(2026, 1, 1) + timedelta(days=days_offset)
    status = random.choice(winter_statuses)
    
    session.execute(
        text("""
            INSERT INTO attendance (child_id, teacher_id, date, status) 
            VALUES (:child_id, :teacher_id, :date, :status)
        """),
        {
            "child_id": child_id,
            "teacher_id": teacher_id,
            "date": date,
            "status": status
        }
    )

print("Создано 80 записей за зиму")

# 2. Генерируем данные ПО ВЫХОДНЫМ — больше прогулов
print("\nГенерирую данные ПО ВЫХОДНЫМ (много прогулов)...")

for i in range(50):
    child_id = random.choice(valid_child_ids)
    teacher_id = random.choice(valid_teacher_ids)
    
    base_date = datetime(2026, 3, 1)
    days_offset = random.randint(0, 90)
    date = base_date + timedelta(days=days_offset)
    
    # Корректируем до субботы/воскресенья
    weekday = date.weekday()
    if weekday < 5:
        days_to_saturday = 5 - weekday
        date = date + timedelta(days=days_to_saturday)
    
    status = random.choice(['ABSENT'] * 8 + ['PRESENT'] * 2)
    
    session.execute(
        text("""
            INSERT INTO attendance (child_id, teacher_id, date, status) 
            VALUES (:child_id, :teacher_id, :date, :status)
        """),
        {
            "child_id": child_id,
            "teacher_id": teacher_id,
            "date": date,
            "status": status
        }
    )

print("Создано 50 записей за выходные")

# 3. Генерируем данные ПО ПЯТНИЦАМ — больше прогулов
print("\nГенерирую данные ПО ПЯТНИЦАМ...")

for i in range(30):
    child_id = random.choice(valid_child_ids)
    teacher_id = random.choice(valid_teacher_ids)
    
    base_date = datetime(2026, 3, 1)
    days_offset = random.randint(0, 90)
    date = base_date + timedelta(days=days_offset)
    
    # Корректируем до пятницы
    weekday = date.weekday()
    days_to_friday = (4 - weekday) % 7
    date = date + timedelta(days=days_to_friday)
    
    status = random.choice(['ABSENT'] * 6 + ['PRESENT'] * 4)
    
    session.execute(
        text("""
            INSERT INTO attendance (child_id, teacher_id, date, status) 
            VALUES (:child_id, :teacher_id, :date, :status)
        """),
        {
            "child_id": child_id,
            "teacher_id": teacher_id,
            "date": date,
            "status": status
        }
    )

print("Создано 30 записей по пятницам")

# 4. Генерируем обычные будни — обычно PRESENT
print("\nГенерирую данные за ОБЫЧНЫЕ БУДНИ...")

for i in range(100):
    child_id = random.choice(valid_child_ids)
    teacher_id = random.choice(valid_teacher_ids)
    days_offset = random.randint(0, 90)
    date = datetime(2026, 3, 1) + timedelta(days=days_offset)
    
    if date.weekday() >= 5:
        continue
    
    status = random.choice(['PRESENT'] * 17 + ['SICK'] * 2 + ['ABSENT'])
    
    session.execute(
        text("""
            INSERT INTO attendance (child_id, teacher_id, date, status) 
            VALUES (:child_id, :teacher_id, :date, :status)
        """),
        {
            "child_id": child_id,
            "teacher_id": teacher_id,
            "date": date,
            "status": status
        }
    )

print("Создано 100 записей за будни")

# Сохраняем
session.commit()

# Статистика
print("\n" + "=" * 60)
print("СТАТИСТИКА ПО СТАТУСАМ:")
print("=" * 60)

result = session.execute(text("""
    SELECT status, COUNT(*) as count 
    FROM attendance 
    GROUP BY status 
    ORDER BY count DESC
"""))

print(f"\n{'Статус':<15} {'Количество':<15}")
print("-" * 30)
for row in result:
    print(f"{row[0]:<15} {row[1]:<15}")

print("\nДАННЫЕ УСПЕШНО СОЗДАНЫ!")
print("\nСЛЕДУЮЩИЕ ШАГИ:")

print("3. Тест дат:")
print("   • 2026-04-04 (Суббота) → 10-40% ⬇️")
print("   • 2026-03-31 (Вторник) → 70-90%")