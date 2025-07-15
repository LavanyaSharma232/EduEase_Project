# 1. Start with a lean, official Python base image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. CRUCIAL: Install FFMPEG using the system package manager
# This is the step that solves the FFMPEG dependency problem.
RUN apt-get update && apt-get install -y ffmpeg

# 4. Copy your requirements file first to leverage Docker's layer caching
COPY requirements.txt .

# 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of your backend code into the container
COPY . .

# 7. Expose the port that FastAPI will run on
EXPOSE 8000

# 8. The command to run when the container starts
# The --host 0.0.0.0 is essential to make it accessible from outside the container.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]