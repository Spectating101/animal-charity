FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY config ./config
COPY scripts ./scripts
RUN mkdir -p /data
ENV AFRN_DB_PATH=/data/relief.db AFRN_RULEPACK=/code/config/rulepacks/tw_dog_cat_pilot.json AFRN_MISSION=/code/config/missions/animal_feed_security.json
EXPOSE 8080
CMD ["fastapi", "run", "app/main.py", "--port", "8080", "--host", "0.0.0.0"]
