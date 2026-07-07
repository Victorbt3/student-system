Deploying to Vercel (Python - Flask)

Quick steps

1. Install Vercel CLI and login:

```bash
npm i -g vercel
vercel login
```

2. From project root run (use `requirements-vercel.txt`):

```bash
# use recommended Python env and requirements
vercel --prod
```

Notes and tips

- This project uses OpenCV for face recognition. OpenCV (opencv-contrib-python) is large and often fails to install in Vercel serverless builders.
- For a simpler serverless deploy, use `requirements-vercel.txt` which omits OpenCV. The app will run in "DEMO/MOCK" mode for face recognition when OpenCV is not present.
- Set environment variables in the Vercel dashboard:
  - `SECRET_KEY` (recommended)
  - `DATABASE_URL` (if you want a production DB; otherwise SQLite will be used under the project root which is ephemeral in serverless)

If you need OpenCV in production, consider deploying with a container-friendly platform (e.g., Render, Fly.io, or Docker-based providers) or using a custom build that provides pre-built OpenCV wheels.
