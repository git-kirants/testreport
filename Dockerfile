FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

COPY reportcardapp-fe480-firebase-adminsdk-wl5o9-55b90068ac.json /app/


# Command to run the application
CMD ["python", "main.py"]
