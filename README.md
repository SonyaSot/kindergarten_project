
## Архитектура

| Компонент | Технология |
|-----------|------------|
| **Backend** | FastAPI (Python 3.11) |
| **Database** | PostgreSQL 15 |
| **AI Module** | scikit-learn, numpy |
| **Containerization** | Docker, Docker Compose |
| **Auth** | JWT (JSON Web Token) |

### Паттерны проектирования (требование 1.6.2):
- **MVC** (Model-View-Controller)
- **Repository** (слой доступа к данным)
- **Service Layer** (слой бизнес-логики)

---

##  Быстрый старт

### Вариант 1: Через Docker (рекомендуется) 

```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-username/kindergarten_project.git
cd kindergarten_project

# 2. Настроить переменные окружения
copy .env.example .env  # Windows
# Отредактировать .env и указать свои пароли

# 3. Запустить систему
docker-compose up --build

# 4. Открыть Swagger документацию
http://127.0.0.1:8000/docs

## Локальный запуск 

# 1. Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить .env
copy .env.example .env

# 4. Запустить сервер
uvicorn app.main:app --reload

# 5. Открыть Swagger
http://127.0.0.1:8000/docs


## Docker команды

# Запуск системы
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up -d

# Остановка
docker-compose down

# Остановка с удалением данных
docker-compose down -v

# Просмотр логов
docker-compose logs -f

# Войти в базу данных
docker-compose exec db psql -U postgres -d kindergarten_db

# Сделать бэкап БД
docker-compose exec db pg_dump -U postgres -d kindergarten_db > backup.sql