# ใช้ base image Python 3.8.2
FROM python:3.8.2

# ตั้งค่า working directory
WORKDIR /app

# คัดลอกไฟล์ requirements.txt
COPY requirements.txt .

# ติดตั้ง dependencies
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx && \
    pip install --no-cache-dir --upgrade -r requirements.txt

# คัดลอกโค้ดทั้งหมดจากโฟลเดอร์ app ไปยัง /app ใน container
COPY ./app /app

# เปิดพอร์ต 8065 สำหรับการเชื่อมต่อ
EXPOSE 8065

# รันคำสั่งเพื่อเริ่มต้นแอปพลิเคชัน
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8065"]
