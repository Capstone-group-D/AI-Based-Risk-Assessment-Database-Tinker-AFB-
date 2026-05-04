FROM python:3.11-slim

# System deps for Levenshtein C extension
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the whole repo so init_db.py can find db/schema.sql and db/seed_data.sql
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r api/requirements.txt

# Download spaCy model at build time
RUN python -m spacy download en_core_web_sm

# Initialize the SQLite database (creates risk_assessment.db at repo root)
RUN python db/init_db.py || true

WORKDIR /app/api

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
