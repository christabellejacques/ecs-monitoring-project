#Start with base image that Python installed
FROM python:3.11-slim

#Set the working directory in the container
WORKDIR /app

#Copy the requirements file into the container
COPY requirements.txt .

#Install the required Python libraries
RUN pip install -r requirements.txt

#Copy the rest of the application code into the container
COPY app/app.py .

#Expose the port that the Flask app will run on
EXPOSE 5000

#When the container starts, run the Flask application
CMD ["python", "app.py"]