FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .

ENV PENNYLANE_API_TOKEN=""
ENV PENNYLANE_COMPANY_ID=""

CMD ["pennylane-mcp"]
