# ARCH.md

## System Architecture — AI VR Tour Guide

### High-Level Diagram
```
Unity VR Client / WebXR / Authoring Studio
   | REST/gRPC / WebSocket
   v
API Gateway (NestJS)
   | gRPC / NATS
   v
Python Workers (ingest, embed, rag, narrate, tts, overlay, bundle, telemetry)
   |
   +-- Postgres (pgvector)
   +-- Redis (cache/state)
   +-- NATS (event bus)
   +-- S3/R2 (assets, bundles, audio)
   +-- ClickHouse (telemetry analytics, optional)
```

### Frontend
**Unity VR Client**  
- Hotspots, overlays (labels, ribbons, ghost reconstructions, heatmaps).  
- Narration avatar with lip-sync (viseme-driven).  
- Comfort manager (teleport, vignette).  
- Tablet UI: subtitles, citations, quizzes.  
- QA client: ask questions with spatial pointer.  

**WebXR Client**  
- react-three-fiber + WebXR API.  
- Lightweight fallback with interactive POIs, overlays, and narration.  

**Web Studio (Next.js)**  
- Anchor/overlay editor with react-three-fiber.  
- Narrative/quiz editor with inline citations.  
- Asset compression + bundle manager.  
- Telemetry dashboards.  

### Backend (NestJS)
- REST/gRPC API surface with OpenAPI 3.1.  
- RBAC with Casbin, RLS by tenant_id.  
- Idempotency-Key, Request-ID headers.  
- Streaming endpoints (TTS, QA) via gRPC/WebSocket.  

### Workers (Python + FastAPI)
- **ingest-worker**: import docs/media, OCR, transcription.  
- **embed-worker**: embeddings upsert into pgvector.  
- **rag-worker**: retrieval, reranking, citation packs.  
- **narrate-worker**: script planning, quiz generation, cultural guardrails.  
- **tts-worker**: voice synthesis + visemes.  
- **overlay-worker**: anchor solving, overlay placement, ghost reconstructions.  
- **bundle-worker**: asset baking, light probes, navmesh, compression.  
- **telemetry-worker**: aggregate dwell/quiz/comfort metrics, generate reports.  

### Eventing
- **NATS Topics**: `doc.ingest`, `index.upsert`, `rag.answer`, `narrate.make`, `tts.synthesize`, `overlay.place`, `bundle.make`, `telemetry.rollup`.  
- **Redis Streams**: ingest progress, session state, telemetry rollups.  

### Data Layer
- **Postgres 16 + pgvector**: tenants, sites, POIs, docs, passages, tours, narratives, overlays, bundles, sessions, events, exports.  
- **Redis**: state caching, throttling, telemetry buffering.  
- **S3/R2**: model/media storage, tour bundles, audio assets.  
- **ClickHouse (optional)**: advanced telemetry queries.  
- **Encryption**: KMS with per-tenant envelopes.  

### Observability & Security
- **Tracing/metrics/logs**: OpenTelemetry.  
- **Dashboards**: Prometheus + Grafana.  
- **Errors**: Sentry.  
- **Security**: SSO/OIDC, license ledger, profanity/cultural sensitivity filters, GDPR compliance.  

### DevOps & Deployment
- **Frontend Studio**: Vercel.  
- **API & Workers**: GKE/Fly/Render, GPU pools for TTS/overlay.  
- **Storage/CDN**: S3/R2 + global CDN for mesh/audio distribution.  
- **CI/CD**: GitHub Actions (lint, typecheck, integration, asset pipeline, deploy).  
