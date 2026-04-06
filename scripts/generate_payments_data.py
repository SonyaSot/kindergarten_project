"""
Генерация тестовых данных об оплатах для AI обучения
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random

engine = create_engine('postgresql://postgres:postgres123@db:5432/kindergarten_db')
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 60)
print(" ГЕНЕРАЦИЯ ДАННЫХ ОБ ОПЛАТАХ")
print("=" * 60)

# Получаем реальные ID детей
result = session.execute(text("SELECT id, group_id FROM children ORDER BY id"))
children_data = [(row[0], row[1]) for row in result]

print(f" Найдено детей: {len(children_data)}")

if len(children_data) == 0:
    print(" Нет детей!")
    exit(1)

# Статусы оплат (80% оплачено вовремя)
statuses = ['paid'] * 8 + ['pending'] + ['overdue']

# Генерируем оплаты за последние 12 месяцев
print("\nГенерирую оплаты за последние 12 месяцев...")

for month_offset in range(12):
    base_date = datetime.now() - timedelta(days=30 * month_offset)
    month_date = base_date.replace(day=1)
    
    for child_id, group_id in children_data:
        # 70% детей имеют оплату каждый месяц
        if random.random() > 0.3:
            payment_date = month_date + timedelta(days=random.randint(1, 25))
            status = random.choice(statuses)
            amount = random.choice([5000, 5000, 5000, 4500, 5500])
            paid_amount = amount if status == 'paid' else 0
            
            session.execute(
                text("""
                    INSERT INTO payments (child_id, month, amount, paid_amount, status, comment)
                    VALUES (:child_id, :month, :amount, :paid_amount, :status, :comment)
                """),
                {
                    "child_id": child_id,
                    "month": month_date,
                    "amount": amount,
                    "paid_amount": paid_amount,
                    "status": status,
                    "comment": f"Оплата за {month_date.strftime('%B %Y')}"
                }
            )

session.commit()

# Статистика
result = session.execute(text("""
    SELECT status, COUNT(*) as count, SUM(paid_amount) as total
    FROM payments
    GROUP BY status
    ORDER BY count DESC
"""))

print("\nСТАТИСТИКА ПО ОПЛАТАМ:")
print(f"\n{'Статус':<15} {'Количество':<15} {'Сумма':<15}")
print("-" * 45)
for row in result:
    status_name = row[0] if row[0] else "unknown"
    count = row[1] if row[1] else 0
    total = row[2] if row[2] else 0
    print(f"{status_name:<15} {count:<15} {total:<15}")

print("\nДАННЫЕ ОБ ОПЛАТАХ СОЗДАНЫ!")
print("\nСЛЕДУЮЩИЕ ШАГИ:")
print("1. Swagger: http://127.0.0.1:8000/docs")
print("2. POST /payments/ai/train → обучить модель")
print("3. GET /payments/ai/predict/group/1 → получить прогноз")