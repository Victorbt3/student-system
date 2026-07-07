# Docker Deployment

This project includes a Docker-based deployment option for full OpenCV support.

## Build and run locally

```bash
docker build -t student-attendance-system .
docker run --rm -p 5000:5000 -e SECRET_KEY=supersecret student-attendance-system
```

## Development with Docker Compose

```bash
docker compose up --build
```

The app will be available at `http://localhost:5000`.

## Notes

- The Docker image installs `opencv-contrib-python` from `requirements.txt`.
- Uploads and local SQLite data are mounted through `./static/uploads`.
- For production, set environment variables in your deployment environment rather than hardcoding secrets.
