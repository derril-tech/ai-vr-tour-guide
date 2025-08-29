AI VR Tour Guide — LangChain agent narrates historical sites in VR with 3D knowledge overlay 

 

1) Product Description & Presentation 

One-liner 

“Walk through history in VR while an AI guide narrates, answers questions, and paints the past with spatial 3D overlays.” 

What it produces 

Immersive tours: scene-by-scene narratives, spatialized audio, subtitles, and sign language avatar (optional). 

3D knowledge overlays: timelines, labels, trade routes, troop movements, architectural phases, artifact callouts—anchored to world geometry. 

Live Q&A: on-device/edge RAG over curated sources; citations surfaced in a holographic card. 

Interactive moments: choice-driven branches, mini-quests, quizzes, photomode. 

Exports: tour packages (.bundle with assets + JSON), session transcripts, comprehension report (PDF), and telemetry JSON. 

Scope/Safety 

Education/entertainment, not legal/archaeological advice. 

Content provenance and cultural sensitivity checks; optional age-appropriate filter. 

Offline-capable tour bundles; online fetch for fresh facts if allowed. 

 

2) Target User 

Museums, heritage sites, tour operators offering premium VR experiences (on-site kiosks or at home). 

Teachers & students for interactive history and geography lessons. 

Travelers & culture fans exploring before/after a trip. 

Game & edtech studios white-labeling tours. 

 

3) Features & Functionalities (Extensive) 

Tour Experience 

Spatial narration: positional audio, gaze-aware cueing, pace adapts to user locomotion. 

Hotspots: diegetic markers reveal facts, models, and then/now transitions. 

Time-scrub: “Rewind/fast-forward” a site through eras (phasing animations). 

Multi-user (optional): synced tours with guide leading and laser-pointer callouts. 

Accessibility: subtitles, transcript tablet, color-safe palettes, locomotion comfort (teleport/snap-turn), motion sickness guard (vignetting). 

Agentic Guidance (LangChain/LangGraph) 

Planner: builds a tour graph from goals (grade level, duration, interests). 

Retriever: hybrid RAG (BM25 + embeddings + reranker) over vetted corpora (site docs, academic summaries, licensed media). 

Narrator: writes scene scripts and ad-libs answers; citation chips appear on demand. 

Tool use: calls OverlayTool to place labels/paths; QuizTool to generate checks-for-understanding; RouteTool to adjust waypoints. 

3D Knowledge Overlays 

Anchoring: planes/meshes (AR-style anchors) with drift correction; occlusion aware. 

Types: labels, ribbons (routes), particle flows (trade/winds), ghost reconstructions, heatmaps (population/fortification strength). 

LOD & perf: adaptive mesh decimation, GPU-instanced props, impostors for far overlays. 

Audio & Speech 

TTS (edge/cloud): natural voice presets, multi-lingual, lip-synced avatar option. 

ASR: “What happened here in 1066?” → live answer with spatial pointer. 

Latency budget: sub-300 ms for cue-on-gaze; streaming TTS for long passages. 

Authoring Tools 

Web Studio: import scans/CAD/photogrammetry, place anchors, write notes, approve sources, set difficulty, test flows. 

Package builder: compress textures, bake light probes, generate navmesh, and export tour.bundle. 

Commerce & Ops 

Licensing: tour SKUs, timed unlocks, seat counts. 

Analytics: dwell time per hotspot, Q&A topics, quiz scores, comfort events. 

Content updates: delta patches; provenance change log. 

 

4) Backend Architecture (Extremely Detailed & Deployment-Ready) 

4.1 Topology 

Clients: 

Unity VR (Quest 2/3/Pro, PCVR/SteamVR, Vision Pro via Unity PolySpatial). 

WebXR fallback (React + react-three-fiber). 

BFF/API: NestJS (Node 20) — REST/gRPC /v1, OpenAPI 3.1, Zod validation, RBAC (Casbin), RLS (tenant/site), Idempotency-Key, Request-ID (ULID). 

Workers (Python 3.11 + FastAPI controller) 

ingest-worker (docs/media import, transcription, OCR) 

embed-worker (chunking, embeddings upsert) 

rag-worker (retrieve, rerank, cite packs) 

narrate-worker (script planning, guardrails, quiz generation) 

tts-worker (voice synth, viseme track) 

overlay-worker (anchor solve, path ribbons, ghost reconstructions) 

bundle-worker (asset bake, light probes, navmesh, compression) 

telemetry-worker (aggregate, reports) 

Event bus: NATS topics (doc.ingest, index.upsert, rag.answer, narrate.make, tts.synthesize, overlay.place, bundle.make, telemetry.rollup) + Redis Streams (progress). 

Data 

Postgres 16 + pgvector (sites, POIs, passages, embeddings, bundles, sessions). 

S3/R2 (models, textures, audio, bundles, thumbnails). 

CDN for static tour bundles & audio streaming. 

Optional: ClickHouse (telemetry analytics). 

Observability: OpenTelemetry (traces/metrics/logs), Prometheus/Grafana dashboards, Sentry errors. 

Secrets: Cloud KMS; per-tenant encryption for content. 

4.2 Data Model (Postgres + pgvector) 

CREATE TABLE tenants (id UUID PRIMARY KEY, name TEXT, plan TEXT, created_at TIMESTAMPTZ DEFAULT now()); 
 
CREATE TABLE sites ( 
  id UUID PRIMARY KEY, tenant_id UUID, title TEXT, location TEXT, era TEXT[], 
  bounds JSONB, default_locale TEXT, created_at TIMESTAMPTZ DEFAULT now() 
); 
 
CREATE TABLE pois ( 
  id UUID PRIMARY KEY, site_id UUID, name TEXT, type TEXT, -- gate|keep|temple|artifact 
  anchor JSONB, -- world pose + mesh refs 
  meta JSONB 
); 
 
CREATE TABLE docs ( 
  id UUID PRIMARY KEY, site_id UUID, title TEXT, kind TEXT, s3_key TEXT, license TEXT, created_at TIMESTAMPTZ DEFAULT now() 
); 
 
CREATE TABLE passages ( 
  id UUID PRIMARY KEY, doc_id UUID, text TEXT, page INT, embedding VECTOR(1536), meta JSONB 
); 
CREATE INDEX ON passages USING hnsw (embedding vector_cosine_ops); 
 
CREATE TABLE tours ( 
  id UUID PRIMARY KEY, site_id UUID, title TEXT, duration_min INT, difficulty TEXT, locales TEXT[], bundle_s3 TEXT, created_at TIMESTAMPTZ DEFAULT now() 
); 
 
CREATE TABLE narratives ( 
  id UUID PRIMARY KEY, tour_id UUID, poi_id UUID, locale TEXT, script TEXT, citations JSONB, quiz JSONB, audio_s3 TEXT, visemes_s3 TEXT 
); 
 
CREATE TABLE overlays ( 
  id UUID PRIMARY KEY, poi_id UUID, kind TEXT, data JSONB, -- label|ribbon|ghost|heatmap 
  lod INT, created_at TIMESTAMPTZ DEFAULT now() 
); 
 
CREATE TABLE sessions ( 
  id UUID PRIMARY KEY, tour_id UUID, user_id UUID, started_at TIMESTAMPTZ, ended_at TIMESTAMPTZ, locale TEXT, comfort JSONB 
); 
 
CREATE TABLE events ( 
  id UUID PRIMARY KEY, session_id UUID, ts TIMESTAMPTZ, kind TEXT, payload JSONB 
); 
 
CREATE TABLE exports ( 
  id UUID PRIMARY KEY, tour_id UUID, kind TEXT, s3_key TEXT, created_at TIMESTAMPTZ DEFAULT now() 
); 
  

Invariants 

RLS by tenant_id. 

Each narratives.script has ≥1 citation; overlays must reference valid anchors. 

Bundles are content-addressed; clients verify via hash before load. 

4.3 API Surface (REST/gRPC /v1) 

Content & RAG 

POST /docs/upload {site_id} → doc.ingest 

GET /search?site_id=...&q=... → cited passages 

POST /narratives/generate {tour_id, poi_id, locale} → script + quiz + citations 

Overlays & Bundles 

POST /overlays/place {poi_id, kind, data} 

POST /bundles/build {tour_id, quality:"high|mobile"} → .bundle (glTF/USDZ, audio, JSON) 

Runtime 

GET /tours/:id/bundle (CDN) 

POST /sessions/start {tour_id} / POST /sessions/:id/end 

POST /qa/ask {session_id, text} → streamed answer + citations 

POST /tts/stream {text, voice, locale} → PCM/Opus chunks + visemes 

Ops 

GET /telemetry/summary?tour_id=... 

POST /exports/report {tour_id, format:"pdf|json"} 

Conventions: Idempotency-Key; Problem+JSON; streaming endpoints via gRPC/WebSocket. 

4.4 Pipelines 

Ingest → clean → chunk → embed → index. 

Author (Web Studio) → anchors & sketch overlays → approve sources. 

Generate narratives & quizzes (LangChain) → synthesize TTS + visemes. 

Build bundle (mesh/texture compression, light probes, navmesh). 

Publish to CDN → version pinning. 

Runtime: client streams TTS/answers + loads overlays on-demand. 

Telemetry: roll-up dwell, quiz, Q&A, comfort → reports. 

4.5 Security & Compliance 

SSO (SAML/OIDC), token scopes (read:tour/play, write:content). 

License ledger per doc/media; profanity/cultural sensitivity filters. 

GDPR delete/export; audit log of content changes. 

 

5) Frontend Architecture (VR-first — Looks Matter) 

5.1 Unity (C#) VR Client 

Packages: XR Interaction Toolkit, OpenXR, Addressables, TextMeshPro, Cinemachine, FMOD/WWISE (optional). 

Scene graph: 

/Scenes 
  Lobby.unity 
  Site_{id}.unity 
/Prefabs 
  Hotspot.prefab           // diegetic marker + proximity trigger 
  Overlay_Label.prefab     // billboard with occlusion + outline 
  Overlay_Route.prefab     // ribbon spline + animated particles 
  Ghost_Rebuild.prefab     // phased construction (shader LOD) 
  NarrationAvatar.prefab   // lip-sync + gaze 
  TimelineRibbon.prefab    // draggable time scrub 
  TabletUI.prefab          // subtitles, citations, quiz 
/Scripts 
  TourManager.cs 
  POIController.cs 
  OverlayController.cs 
  NarrationController.cs   // TTS stream + lipsync (visemes) 
  QAClient.cs              // ask/answer with pointer 
  ComfortManager.cs        // vignette & locomotion 
  TelemetryClient.cs 
  LocalizationManager.cs 
  

Visual design: glassy holographic cards, soft neon accents, subtle bloom; diegetic UI (tablet/panel you hold). 

Performance: baked light probes, GPU instancing, dynamic resolution, occlusion culling. 

5.2 Web Studio (Next.js 14) 

shadcn/ui + Tailwind, Framer Motion for smooth spatial previews. 

Pages: 

/sites (CRUD) 

/author/[siteId] (3D editor with react-three-fiber, anchor gizmos) 

/tours/[tourId] (flow graph, narrative editor, quiz builder) 

/assets (media manager, compression) 

/publish (bundle status, CDN links) 

Components: AnchorGizmo, RibbonEditor, GhostPhasePanel, ScriptEditor (citations inline), QuizDesigner, BundleStatus, TelemetryDash. 

5.3 Accessibility & i18n 

Multilingual subtitles, dyslexia-friendly font option. 

Controller + hand-tracking; seated/standing modes. 

High-contrast theme; scalable UI. 

 

6) SDKs & Integration Contracts 

Generate a narrative for a POI 

POST /v1/narratives/generate 
{ "tour_id":"UUID","poi_id":"UUID","locale":"en-US","style":"story+scholarly" } 
  

Stream TTS (client pulls) 

POST /v1/tts/stream 
{ "text":"The citadel was rebuilt in 1230...", "voice":"guide_f","locale":"en-GB","format":"opus" } 
  

Ask a question in-tour 

POST /v1/qa/ask 
{ "session_id":"UUID","text":"Why was the western wall thicker?" } 
  

Fetch overlays for a POI 

GET /v1/overlays?poi_id=UUID&lod=mobile 
  

Start/End session 

POST /v1/sessions/start { "tour_id":"UUID","locale":"fr-FR" } 
POST /v1/sessions/{id}/end 
  

Export tour bundle 

POST /v1/exports/report { "tour_id":"UUID","format":"pdf" } 
  

JSON bundle keys: sites[], pois[], passages[], tours[], narratives[], overlays[], bundles[], sessions[], events[]. 

 

7) DevOps & Deployment 

FE (Studio): Vercel (Next.js). 

API/Workers: GKE/Fly/Render; dedicated pools for embed/tts/bundle. 

DB: Managed Postgres + pgvector; PITR; read replicas. 

Storage/CDN: S3/R2 + global CDN (range requests for audio/meshes). 

Queues/Cache: NATS + Redis. 

CI/CD: GitHub Actions (lint/typecheck/unit/integration, asset pipeline, image scan, sign, deploy). 

SLOs 

RAG answer (cached) < 250 ms p95; cold < 900 ms 

TTS start (first byte) < 400 ms p95 

Bundle download (mobile) < 6 s p95 on 50 Mbps 

CPU/GPU frame time steady at < 13.3 ms (75 Hz targets) 

 

8) Testing 

Unit: anchor math, ribbon spline sampling, viseme alignment, RAG citation presence. 

Integration: ingest → embed → generate → TTS → bundle → client load. 

VR E2E: automated headset sims (Quest link) — teleport loops, hotspot triggers, quiz flow, QA latency. 

Perf: shader overdraw, draw calls, LOD switching; CPU/GPU frame budgets. 

Content QA: cultural sensitivity/language checks; profanity/unsafe flagging. 

Load/Chaos: CDN throttling, packet loss on TTS; fallback to on-device cache. 

Security: RLS tests; license enforcement; audit completeness. 

 

9) Success Criteria 

Product KPIs 

Average dwell time per POI ≥ 45 s; tour completion ≥ 70%. 

Comprehension uplift (quiz correct) +25% vs non-guided control. 

Q&A helpfulness rating ≥ 4.5/5. 

Repeat play (another tour within 7 days) ≥ 30%. 

Engineering SLOs 

Citation coverage in narrator answers ≥ 90%. 

TTS underruns < 0.5%; QA latency p95 < 700 ms. 

Crash-free sessions ≥ 99.5%. 

 

10) Visual/Logical Flows 

A) Authoring 

 Import site mesh → place POIs/anchors → add overlays (labels/ribbons/ghosts) → RAG approve sources → generate narratives → build bundle → publish. 

B) Player Start 

 Download bundle → calibrate scale → show intro → start session. 

C) Explore 

 Enter POI → auto-cue (spatial audio + subtitles) → overlays animate in → user asks questions → agent answers with citation chips. 

D) Branch & Learn 

 Timeline ribbon → scrub era → overlays morph → optional quiz → score shown on tablet. 

E) Wrap 

 Outro → comprehension report → session & transcript export → prompt next tour. 

 

 