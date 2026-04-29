FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your code
COPY . .

# THIS IS THE IMPORTANT PART:
# No CMD here, because docker-compose overrides it