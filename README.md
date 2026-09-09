# StudySprint — Render Ready

## Deploy on Render
1. Put this project in a GitHub repository.
2. In Render, choose **New → Blueprint** and connect the repository.
3. Render reads `render.yaml` and creates:
   - a Python web service
   - a PostgreSQL database
4. When asked for `ADMIN_PASSWORD`, create a strong password.
5. Deploy. Render will provide a public `onrender.com` URL.

## Important
- Do not use `admin123` in production.
- The database is PostgreSQL in Render.
- Student attempts are stored server-side.
- Use HTTPS (Render provides it for the public service).
- The current seed bank is a small demo bank. Add your real Class/Subject/Chapter questions from the Admin panel.

## Local
`pip install -r requirements.txt`
Set `DATABASE_URL` (or let the app fall back to SQLite locally), set `SECRET_KEY`, then:
`python app.py`
