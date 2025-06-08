# A2A Stock Management System Docker Configuration

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libaio1 \
    && rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basiclite-linuxx64.zip \
    && unzip instantclient-basiclite-linuxx64.zip \
    && rm instantclient-basiclite-linuxx64.zip \
    && mv instantclient_* /opt/oracle \
    && echo /opt/oracle >> /etc/ld.so.conf \
    && ldconfig

# Set Oracle environment variables
ENV ORACLE_HOME=/opt/oracle
ENV LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH
ENV PATH=$ORACLE_HOME:$PATH

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs config

# Set default configuration if not provided
RUN if [ ! -f config/config.yaml ]; then \
        python -c "from config.config import Config; Config()"; \
    fi

# Expose port for web interface (if implemented)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the application
CMD ["python", "main.py"]

# Docker build command:
# docker build -t a2a-stock-management .

# Docker run command:
# docker run -d \
#   --name a2a-stock-system \
#   -v $(pwd)/config:/app/config \
#   -v $(pwd)/logs:/app/logs \
#   -p 8080:8080 \
#   a2a-stock-management

# Docker compose example:
# version: '3.8'
# services:
#   a2a-stock-management:
#     build: .
#     container_name: a2a-stock-system
#     volumes:
#       - ./config:/app/config
#       - ./logs:/app/logs
#     ports:
#       - "8080:8080"
#     environment:
#       - ORACLE_HOST=oracle-db
#       - ORACLE_PASSWORD=${DB_PASSWORD}
#       - EMAIL_PASSWORD=${EMAIL_PASSWORD}
#     depends_on:
#       - oracle-db
#     restart: unless-stopped
#
#   oracle-db:
#     image: container-registry.oracle.com/database/express:21.3.0-xe
#     container_name: oracle-xe
#     ports:
#       - "1521:1521"
#     environment:
#       - ORACLE_PWD=${ORACLE_PWD}
#     volumes:
#       - oracle-data:/opt/oracle/oradata
#     restart: unless-stopped
#
# volumes:
#   oracle-data: