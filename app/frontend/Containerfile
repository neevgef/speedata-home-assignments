FROM python:3.14.5

WORKDIR /app/backend

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD python main.py

EXPOSE 8000:8000