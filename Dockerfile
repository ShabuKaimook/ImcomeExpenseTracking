# 1. ใช้ Python Image แบบ Slim เพื่อให้ขนาดเล็กและประหยัดพื้นที่
FROM python:3.11-slim

# 2. ตั้งค่า Environment Variables
# PYTHONDONTWRITEBYTECODE: ป้องกันไม่ให้ Python สร้างไฟล์ .pyc
# PYTHONUNBUFFERED: ช่วยให้ Log แสดงผลใน Terminal ทันที (Real-time)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. ติดตั้ง Dependencies ของระบบ (เช่น Tesseract OCR และ Library สำหรับแต่งรูป)
# ต้องติดตั้งผ่าน apt-get เพราะ Python library (Pillow/PyTesseract) ต้องใช้ตัวนี้รัน
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-tha \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 4. ตั้งค่า Working Directory ใน Container
WORKDIR /app

# 5. คัดลอก requirements.txt และติดตั้ง Python Dependencies
# แยกการ copy requirements ออกมาเพื่อให้ Docker ทำ Caching ได้ (Build ครั้งต่อไปจะเร็วมาก)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. คัดลอกโค้ดทั้งหมดเข้าไปใน Container
COPY . .

# 7. เปิด Port 8000 (ตามที่ตั้งไว้ใน uvicorn)
EXPOSE 8000

# 8. คำสั่งรัน Server
# ใช้ "main:app" โดยที่ main คือชื่อไฟล์ main.py และ app คือตัวแปร FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]