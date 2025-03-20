FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variable
ENV VERBOSE=0
ENV NODES=0
ENV WAYS=0
ENV RELATIONS=0
ENV TAGS=0

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY consumer.py .

# Run the script
CMD ["python", "consumer.py"]
