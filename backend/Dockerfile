FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project definition
COPY pyproject.toml .

# Install dependencies
# We use pip to install directly from pyproject.toml as it supports it (PEP 517)
# or we can install poetry. For simplicity, let's use pip with the .
# First we need to make sure we have the source code structure ready for pip install .
# But since we are in dev mode, we usually install dependencies.

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false

# Install production dependencies
COPY . .
RUN poetry install --without dev

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
