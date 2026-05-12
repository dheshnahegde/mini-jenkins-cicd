FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your code (Make sure there is only ONE dot here)
COPY . .

# (Optional) No CMD here as docker-compose overrides it