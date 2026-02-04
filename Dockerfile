FROM python:3.9-slim

WORKDIR /app

# 🔴 التعديل: استبدلنا المكتبة القديمة بالجديدة (libgl1)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 🔴 التعديل: زودنا أمر عشان يسرع التحميل وما يهنجش
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
