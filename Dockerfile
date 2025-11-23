# Orion Application Dockerfile
# Uses Conda for dependency management

FROM continuumio/miniconda3:latest

# Set working directory
WORKDIR /app

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy environment file
COPY environment.yml .

# Create conda environment
RUN conda env create -f environment.yml && \
    conda clean -afy

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "orion", "/bin/bash", "-c"]

# Copy and build downloader service
COPY services/downloader/ ./services/downloader/
RUN cd services/downloader && npm install && npm run build

# Copy application code
COPY src/ ./src/
COPY setup.py ./
COPY orion ./

# Set Python path and environment
ENV PYTHONPATH=/app
ENV PATH="/opt/conda/envs/orion/bin:$PATH"
ENV CONDA_DEFAULT_ENV=orion

# Create data directories
RUN mkdir -p /app/data /app/Edgar_filings /app/metadata

# Default command
CMD ["python", "-m", "src.cli", "--help"]

