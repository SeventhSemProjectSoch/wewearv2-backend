FROM python:3.11-alpine
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=venv
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml .
COPY uv.lock .
RUN uv sync --no-cache-dir
COPY ./backend/manage.py .
COPY ./backend/project project
COPY ./backend/core core
EXPOSE 8000
CMD ["/bin/sh", "-c", "source venv/bin/activate;python manage.py collectstatic --noinput;python manage.py migrate;gunicorn --bind 0.0.0.0:8000 --workers=1 --env DJANGO_SETTINGS_MODULE=project.settings project.wsgi"]
