# TODO.md

## Development Roadmap

### Phase 1: Foundations & Infrastructure
- [x] Initialize monorepo (Unity client, Web Studio, API, workers).  
- [x] Set up NestJS API Gateway with REST/gRPC, OpenAPI, Casbin RBAC, RLS.  
- [x] Configure Postgres + pgvector, Redis, NATS, and S3/R2 via Docker Compose.  
- [x] Establish GitHub Actions CI/CD (lint, typecheck, tests, asset pipeline).  
- [x] Implement authentication (SSO/OIDC, token scopes).  
- [x] Implement Unity VR client (scene graph, hotspots, narration avatar, overlays, comfort manager).  
- [x] Build WebXR fallback client (react-three-fiber).  
- [x] Authoring Studio: CRUD sites, anchors, overlays, tour flow graph, quiz designer.  
- [x] Ingest pipeline: docs/media → OCR/transcription → embeddings (embed-worker).  
- [x] Overlay/anchor placement system with occlusion awareness, adaptive LOD.  
- [x] Bundle pipeline: asset compression, navmesh bake, light probes, glTF/USDZ export.  

### Phase 2: Agentic Guidance & Narration
- [x] Implement LangChain/LangGraph planner, retriever, narrator agents.  
- [x] RAG worker: hybrid retrieval (BM25 + embeddings + reranker) with vetted sources.  
- [x] Narration generation with citations + quiz injection.
- [x] TTS worker with multilingual voice + viseme tracks for lip-sync.
- [x] QA client: in-VR pointer + ASR → real-time answer with holographic citation chips.
- [x] Guardrails: cultural sensitivity/profanity filters, citation enforcement.
- [x] Hotspots: interactive markers with branching narratives.
- [x] Timeline ribbon for time-scrubbing eras.  
- [x] Multiplayer (optional): synced tours with guide pointer.
- [x] Telemetry worker: dwell time, comfort events, quiz scores → aggregate reports.
- [x] Exports: tour.bundle, PDF comprehension reports, JSON telemetry.
- [x] Commerce & licensing (SKUs, timed unlocks, seat counts).  

### Phase 3: Privacy, Testing & Deployment
- [x] Implement encryption envelopes per tenant; GDPR delete/export.
- [x] Enforce RLS by tenant_id; license ledger for media.
- [x] Accessibility: subtitles, dyslexia-friendly fonts, hand-tracking, high-contrast modes.
- [x] Testing: unit (anchors, visemes, retrieval), integration (end-to-end ingest→bundle), VR E2E (Quest link sims), chaos (network loss, CDN throttling).
- [x] Deploy Studio frontend to Vercel, API + workers to GKE/Fly/Render.
- [x] Configure monitoring dashboards and alerting (OpenTelemetry, Grafana, Sentry).  
