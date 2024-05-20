FROM python:3.12.3-slim-bookworm

RUN apt update && apt upgrade -y

RUN apt install tesseract-ocr tesseract-ocr-eng -y

WORKDIR app/

COPY src/ src/
COPY main.py .
COPY requirements.txt .
COPY .env .

RUN pip install -r requirements.txt

CMD ["python3", "main.py"]