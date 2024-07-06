# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /app/imaginify/requirements.txt

# Make port 8185 available to the world outside this container
EXPOSE 8185

# Define environment variable
ENV FLASK_APP=/app/imaginify/main.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run main.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0", "--port=8185"]