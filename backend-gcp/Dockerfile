FROM python:3.10

# Set the working directory
WORKDIR /app

# RUN apt-get update &&\
#     apt-get install -y binutils libproj-dev gdal-bin

# Copy the requirements.txt file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Specify the command to run your application
CMD ["python", "main.py"]
