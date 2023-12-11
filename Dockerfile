# Use the official Python base image
FROM python:3

# Install Bluetooth-related packages
RUN apt-get update && \
    apt-get install -y gpsd && \
    apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the Python dependencies file
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script and settings file to the container
COPY gps2mqtt.py .
COPY settings.py .
COPY helpers.py .

# Run the Python script as the default command
CMD ["python3", "gps2mqtt.py"]
