# Sovereign Ecosystem Ω — Multi-stage Production Build
# From lab to life — for everyone.

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Web Builder
FROM node:20-slim AS web-builder

WORKDIR /web
COPY 02_GALAXY_A17_SOVEREIGN_Ω/web/package.json .
COPY 02_GALAXY_A17_SOVEREIGN_Ω/web/package-lock.json .
RUN npm ci

COPY 02_GALAXY_A17_SOVEREIGN_Ω/web/ .
RUN npm run build

# Stage 3: Production
FROM python:3.11-slim AS production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY 01_ACCIO_WORK_PLATFORM/ ./01_ACCIO_WORK_PLATFORM/
COPY 07_QUANTUM_MESH_CORE/ ./07_QUANTUM_MESH_CORE/
COPY 10_SOVEREIGN_E1_TECH_PACK/ ./10_SOVEREIGN_E1_TECH_PACK/
COPY 12_SOVEREIGN_MEDICAL_SIM/ ./12_SOVEREIGN_MEDICAL_SIM/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY docs/ ./docs/

# Copy web build
COPY --from=web-builder /web/dist ./02_GALAXY_A17_SOVEREIGN_Ω/web/dist

# Copy quantum constants
COPY 02_GALAXY_A17_SOVEREIGN_Ω/QUANTUM_CONSTANTS.json ./02_GALAXY_A17_SOVEREIGN_Ω/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV QUANTUM_COHERENCE=0.947
ENV QUANTUM_NODES=20000000
ENV QUANTUM_SIGNATURE=SOVEREIGN_Ω

# Expose ports
EXPOSE 5000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/status || exit 1

# Entry point
CMD ["python3", "-m", "scripts.deploy_production"]