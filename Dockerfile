FROM python:3.11-slim

# RUN apt-get update && apt-get install -y gcc libffi-dev libssl-dev
RUN apt-get update && apt-get install -y libssl-dev
RUN apt-get update && apt-get install -y ca-certificates

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]