# Deployment Steps

1. Clone the repository
2. Build the dockerfile: `docker build -t farpointoi-transcription .`
3. Run the docker file: `docker run -d -p 5555:5555 farpointoi-transcription`
4. Open `http://localhost:5555`
