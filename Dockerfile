# نستخدم نسخة بايثون خفيفة وسريعة
FROM python:3.9-slim

# نجهز مكان الشغل جوه السيرفر
WORKDIR /app

# 🔴 التعديل المهم: تحميل مكتبات الفيديو اللي كانت بتعمل مشاكل
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف الطلبات وتحميلها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الكود
COPY . .

# أمر التشغيل
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
