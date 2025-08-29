# PLAN.md

## Product: AI VR Tour Guide (LangChain Agent + 3D Knowledge Overlay)

### Vision & Goals
Deliver immersive VR tours where an **AI agent narrates historical sites**, overlays 3D contextual knowledge (timelines, routes, reconstructions), and enables live Q&A with citations. Users can explore interactively, branch into mini-quests, and export session reports.

### Key Objectives
- Immersive VR tours with narration, overlays, quizzes, and photomode.
- Live agentic Q&A (LangChain RAG over vetted corpora).
- Authoring studio for museums/educators to create & publish tours.
- Exportable reports (bundles, transcripts, comprehension results).
- Multi-platform deployment: Unity VR, WebXR, and authoring web studio.

### Target Users
- Museums, heritage sites, cultural institutions.
- Schools and educators (interactive history/geography lessons).
- Travelers and culture fans exploring before/after trips.
- Studios offering white-label cultural VR content.

### High-Level Approach
1. **Frontend**
   - Unity VR client (Quest, PCVR, Vision Pro).  
   - WebXR fallback (React + react-three-fiber).  
   - Authoring Studio (Next.js 14 + shadcn/ui + react-three-fiber).  

2. **Backend**
   - NestJS API Gateway (REST/gRPC, RBAC, RLS).  
   - Python workers: ingest, embed, RAG, narrate, TTS, overlay, bundle, telemetry.  
   - Postgres + pgvector, Redis, NATS, S3/R2, optional ClickHouse for telemetry.  

3. **DevOps**
   - GKE/Fly/Render backend, Vercel Studio frontend.  
   - CI/CD via GitHub Actions.  
   - Monitoring: OpenTelemetry, Prometheus, Grafana, Sentry.  

### Success Criteria
- **Product KPIs**:  
  - Dwell time ≥ 45s/POI, completion ≥ 70%.  
  - Quiz comprehension uplift +25%.  
  - Q&A helpfulness ≥ 4.5/5.  
  - Repeat play ≥ 30%.  

- **Engineering SLOs**:  
  - RAG answer p95 < 900 ms cold, < 250 ms cached.  
  - TTS start < 400 ms p95.  
  - Crash-free sessions ≥ 99.5%.  
  - QA latency p95 < 700 ms.

## Phase 1 Progress Summary

### ✅ Completed Infrastructure & Foundations
1. **Monorepo Structure**: Complete turbo-based monorepo with apps (API, Studio, WebXR, Unity, Workers) and shared packages
2. **NestJS API Gateway**: Full REST/gRPC API with OpenAPI docs, JWT/OIDC auth, Casbin RBAC, tenant isolation
3. **Infrastructure**: Docker Compose setup with Postgres+pgvector, Redis, NATS, MinIO, monitoring stack
4. **CI/CD**: GitHub Actions workflows for TypeScript/Python linting, testing, building, and deployment
5. **Authentication**: JWT + OIDC SSO with role-based permissions and tenant guards
6. **WebXR Client**: React Three Fiber VR/AR client with hotspots, spatial audio, and fallback controls
7. **Authoring Studio**: Next.js 14 dashboard with shadcn/ui for site management and tour creation

### 🏗️ Architecture Highlights
- **Multi-tenant**: Row-level security with tenant isolation
- **Type-safe**: Shared TypeScript types across all applications
- **Scalable**: Microservices architecture with event-driven communication
- **Observable**: OpenTelemetry tracing, Prometheus metrics, structured logging
- **Secure**: RBAC, OIDC integration, encrypted secrets, HTTPS everywhere

### 📊 Current Status
- **Phase 1**: 10/10 tasks completed (100%) ✅
- **Phase 2**: 10/10 tasks completed (100%) ✅
- **Phase 3**: 6/6 tasks completed (100%) ✅
- **ALL PHASES COMPLETE**: 26/26 tasks (100%) 🎉
- **Major Completions**: 
  - ✅ Complete Unity VR client with advanced comfort management
  - ✅ Enterprise-grade privacy with tenant encryption & GDPR compliance
  - ✅ Comprehensive accessibility support (visual, hearing, motor, cognitive)
  - ✅ Full testing suite (unit, integration, E2E, VR, chaos engineering)
  - ✅ Production monitoring with 15+ alert rules and health dashboards
  - ✅ Deployment-ready architecture for Vercel/GKE/Fly/Render
- **Status**: 🚀 **COMPLETE AI VR TOUR GUIDE PLATFORM** 🚀  
