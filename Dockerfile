# Sử dụng Python 3.11
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy code vào container
COPY . /app

# Cài thư viện
RUN pip install --no-cache-dir -r requirements.txt

# Chạy bot
CMD ["python", "bot.py"]