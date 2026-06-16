# LETI EDU Matematika Mentor Bot — yangi spec (leti_math_mentor paketi)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Avval kutubxonalar (Docker cache uchun alohida qatlam)
COPY leti_math_mentor/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Keyin kod
COPY leti_math_mentor ./leti_math_mentor
COPY run_mentor.py ./run_mentor.py

# .env image ichiga KIRMAYDI — qiymatlar docker-compose env_file orqali beriladi.
CMD ["python", "run_mentor.py"]
