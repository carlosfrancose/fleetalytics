FROM python:3.11-slim                # Start with Python image

WORKDIR /app                         # Set working directory inside container

COPY requirements.txt .              # Copy dependency list
RUN pip install --no-cache-dir -r requirements.txt   # Install dependencies

COPY ./app ./app                     # Copy application source code

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]  # Start the app