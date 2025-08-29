# Unity VR Client

This directory contains the Unity VR client for the AI VR Tour Guide.

## Features
- VR support for Quest, PCVR, and Vision Pro
- Interactive hotspots and overlays
- Narration avatar with lip-sync
- Comfort management (teleport, vignette)
- In-VR Q&A interface
- Spatial audio and haptic feedback

## Setup
1. Open this directory in Unity 2022.3 LTS or later
2. Install XR Interaction Toolkit
3. Configure XR settings for target platforms
4. Import required packages from Package Manager

## Architecture
- Scene graph with hotspots and anchors
- Overlay system with adaptive LOD
- Narration system with viseme-driven lip-sync
- Comfort manager for motion sickness prevention
- Network client for API communication

## Build Targets
- Meta Quest (Android)
- PCVR (Windows)
- Apple Vision Pro (visionOS)
