FROM python:3.9-slim

WORKDIR /app

# 🔴 التعديل: ضفنا مكتبات زيادة (sm6, xext6) عشان نأمن نفسنا تماماً
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# تحديث pip وتحميل الطلبات
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
