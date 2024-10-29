# Use official Python image
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project to the container
COPY . .

# Expose the port if you plan to add an API endpoint in the future
EXPOSE 8081

# Run the retraining script
CMD ["python", "retrain_yolo.py"]