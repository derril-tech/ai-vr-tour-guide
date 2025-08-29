# AI VR Tour Guide Workers

Python-based microservices for AI VR Tour Guide processing pipeline.

## Workers

### Core Workers
- **ingest-worker**: Document/media import, OCR, transcription
- **embed-worker**: Text embeddings generation and vector storage
- **rag-worker**: Retrieval-augmented generation with citations
- **narrate-worker**: Script planning and quiz generation
- **tts-worker**: Text-to-speech synthesis with visemes
- **overlay-worker**: 3D anchor placement and overlay generation
- **bundle-worker**: Asset compression and tour packaging
- **telemetry-worker**: Analytics aggregation and reporting

## Architecture

Each worker is a FastAPI microservice that:
- Subscribes to NATS topics for async processing
- Uses Redis for caching and state management
- Connects to PostgreSQL with pgvector for data storage
- Implements OpenTelemetry for observability
- Follows structured logging with correlation IDs

## Development

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Run a worker
uvicorn src.workers.ingest.main:app --reload --port 8001
```

## Configuration

Workers are configured via environment variables:
- Database: `DATABASE_URL`
- Redis: `REDIS_URL` 
- NATS: `NATS_URL`
- Storage: `S3_*` variables
- AI APIs: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.

## Deployment

Workers can be deployed as:
- Docker containers in Kubernetes
- Serverless functions (AWS Lambda, Google Cloud Functions)
- Traditional VMs with systemd services
