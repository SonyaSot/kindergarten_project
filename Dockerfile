FROM python:3.11

WORKDIR /app

COPY requirements.txt .

# Увеличиваем тайм-аут и используем кэш
RUN pip install --no-cache-dir \
    --default-timeout=1000 \
    --retries 5 \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host pypi.python.org \
    -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]