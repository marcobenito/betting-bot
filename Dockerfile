FROM python:3.9.13-alpine3.16

WORKDIR /app

# Install requirements
COPY requirements.txt .
# First line is necessary for Pillow to be installed
RUN apk add zlib-dev jpeg-dev gcc musl-dev \
    && pip install -r requirements.txt \
    && apk update \
    && apk add tesseract-ocr \
    && apk add tesseract-ocr-data-spa

COPY . .

EXPOSE 5000

CMD ["python3","run.py"]

