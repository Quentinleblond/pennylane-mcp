FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN if [ ! -d pennylane_mcp ]; then \
        mkdir -p pennylane_mcp && \
        mv server.py pennylane_mcp/ && \
        mv client.py pennylane_mcp/ && \
        mv __init__.py pennylane_mcp/; \
    fi

RUN pip install --no-cache-dir -e .

CMD ["pennylane-mcp"]
