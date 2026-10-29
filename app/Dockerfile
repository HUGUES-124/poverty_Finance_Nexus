FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PORT=8000 DATA_DIR=/data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data && useradd -m app && chown -R app /app /data
USER app
VOLUME /data
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request as u;u.urlopen('http://localhost:8000/health')"
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60
