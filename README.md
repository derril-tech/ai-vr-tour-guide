# 🚀 AI VR Tour Guide Platform

> **Next-generation immersive educational experiences powered by AI and VR/AR technology**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Unity](https://img.shields.io/badge/Unity-100000?logo=unity&logoColor=white)](https://unity.com/)
[![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![NestJS](https://img.shields.io/badge/NestJS-E0234E?logo=nestjs&logoColor=white)](https://nestjs.com/)

## 🌟 What is AI VR Tour Guide?

**AI VR Tour Guide** is a revolutionary platform that transforms how people learn about and explore cultural sites, museums, historical locations, and educational content. By combining cutting-edge artificial intelligence with immersive VR/AR technology, we create personalized, interactive, and deeply engaging educational experiences that adapt to each learner's needs and interests.

Think of it as having a **brilliant, knowledgeable guide** who never gets tired, speaks every language, remembers everything about every artifact, and can instantly answer any question while providing an immersive journey through time and space.

## 🎯 What Does It Do?

### **🤖 AI-Powered Intelligent Guidance**
- **Smart Narration**: AI agents generate contextual, personalized narratives based on user interests and learning style
- **Real-Time Q&A**: Ask questions naturally using voice or gesture, get instant answers with visual citations
- **Adaptive Learning**: Content difficulty and pacing automatically adjust to user comprehension and engagement
- **Multi-Language Support**: Seamless translation and culturally-aware content delivery

### **🥽 Immersive VR/AR Experiences**
- **Time Travel**: Experience historical sites as they were in different eras with accurate reconstructions
- **Interactive Exploration**: Touch, examine, and manipulate virtual artifacts and environments
- **Spatial Learning**: Walk through ancient buildings, witness historical events, explore impossible spaces
- **Cross-Platform**: Works on VR headsets (Quest, PICO), AR devices (HoloLens), and web browsers

### **📚 Rich Educational Content**
- **Contextual Information**: Layered information appears when and where it's most relevant
- **Interactive Quizzes**: Gamified learning with immediate feedback and progress tracking
- **Citation-Backed Facts**: Every piece of information is sourced and verifiable with academic references
- **Multimedia Integration**: Combine 3D models, historical documents, audio, video, and interactive elements

### **👥 Collaborative Learning**
- **Multiplayer Tours**: Explore together with friends, family, or classmates in shared virtual spaces
- **Guided Sessions**: Teachers and experts can lead live tours for groups
- **Social Features**: Share discoveries, discuss findings, and learn from others
- **Accessibility First**: Full support for visual, hearing, motor, and cognitive accessibility needs

## 🌈 Benefits & Impact

### **🎓 For Learners**
- **Personalized Education**: Content adapts to your learning style, pace, and interests
- **Unlimited Access**: Visit any location, anytime, without travel costs or physical limitations
- **Deep Engagement**: Interactive experiences create lasting memories and better retention
- **Safe Exploration**: Examine fragile artifacts and dangerous locations without risk
- **Inclusive Learning**: Accessibility features ensure everyone can participate fully

### **🏛️ For Cultural Institutions**
- **Global Reach**: Share collections and knowledge with worldwide audiences
- **Enhanced Visitor Experience**: Supplement physical visits with rich digital layers
- **Preservation**: Create permanent digital records of artifacts and spaces
- **Revenue Generation**: New monetization opportunities through virtual experiences
- **Data Insights**: Understand visitor engagement and optimize exhibits

### **🎒 For Educators**
- **Immersive Curriculum**: Bring any subject to life with virtual field trips
- **Differentiated Learning**: Automatically adapt to diverse student needs
- **Assessment Tools**: Built-in quizzes and analytics track learning progress
- **Resource Efficiency**: Reduce costs while expanding educational opportunities
- **Professional Development**: Access expert knowledge and best practices

### **🌍 For Society**
- **Democratic Access**: Make world-class education available to everyone, everywhere
- **Cultural Preservation**: Safeguard heritage for future generations through digital twins
- **Environmental Impact**: Reduce travel-related carbon emissions
- **Economic Opportunity**: Create new jobs in digital content creation and VR education
- **Global Understanding**: Foster cross-cultural learning and empathy

## 🏗️ Architecture Overview

Built on a modern, scalable microservices architecture:

- **🎮 Unity VR Client**: Native VR experiences with advanced comfort management
- **🌐 WebXR Client**: Cross-platform VR/AR accessible via web browsers
- **🎨 Authoring Studio**: Next.js-based content creation and management platform
- **🔧 NestJS API Gateway**: Robust backend with REST/GraphQL APIs and real-time features
- **🤖 AI Worker Services**: LangChain/LangGraph agents for intelligent content generation
- **📊 Analytics & Telemetry**: Comprehensive learning analytics and experience optimization
- **🔒 Enterprise Security**: GDPR-compliant with tenant isolation and encryption

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Docker and Docker Compose
- Unity 2022.3+ (for VR client development)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/ai-vr-tour-guide.git
   cd ai-vr-tour-guide
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development environment**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   npm run dev
   ```

4. **Access the applications**
   - 🎨 **Authoring Studio**: http://localhost:3000
   - 🌐 **WebXR Client**: http://localhost:5173
   - 🔧 **API Documentation**: http://localhost:3001/api
   - 📊 **Database Admin**: http://localhost:5050

### Environment Setup

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Key environment variables:
```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/vr_tour_guide

# Redis
REDIS_URL=redis://localhost:6379

# Storage (MinIO for development)
S3_ENDPOINT=http://localhost:9000
S3_BUCKET_NAME=vr-tours
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# Authentication
JWT_SECRET=your-super-secret-jwt-key
OIDC_CLIENT_ID=your-oidc-client-id
OIDC_CLIENT_SECRET=your-oidc-client-secret

# AI Services
OPENAI_API_KEY=your-openai-api-key
LANGCHAIN_API_KEY=your-langchain-api-key
```

## 📖 Documentation

- **[API Documentation](./docs/api.md)** - Complete API reference and examples
- **[Architecture Guide](./docs/architecture.md)** - System design and component overview
- **[Content Creation Guide](./docs/content-creation.md)** - How to create tours and experiences
- **[Deployment Guide](./docs/deployment.md)** - Production deployment instructions
- **[Contributing Guide](./CONTRIBUTING.md)** - How to contribute to the project

## 🧪 Testing

Run the complete test suite:

```bash
# Unit tests
npm run test

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# VR-specific tests
npm run test:vr

# All tests with coverage
npm run test:all
```

## 🚀 Deployment

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Production

**Quick Deploy Options:**

- **Railway**: Connect GitHub repo, add environment variables, deploy
- **Fly.io**: `fly launch` and `fly deploy`
- **Vercel + Supabase**: Frontend on Vercel, backend on Supabase
- **AWS/GCP/Azure**: Full Kubernetes deployment with Terraform

See our [Deployment Guide](./docs/deployment.md) for detailed instructions.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details on:

- Code of Conduct
- Development workflow
- Pull request process
- Coding standards
- Testing requirements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT and embedding models
- **LangChain** for AI agent orchestration
- **Unity Technologies** for VR development tools
- **Meta** for WebXR standards and Quest platform
- **The open-source community** for the amazing tools and libraries

## 📞 Support & Contact

- **Documentation**: [docs.ai-vr-tour-guide.com](https://docs.ai-vr-tour-guide.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/ai-vr-tour-guide/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/ai-vr-tour-guide/discussions)
- **Email**: support@ai-vr-tour-guide.com
- **Discord**: [Join our community](https://discord.gg/ai-vr-tour-guide)

---

**Made with ❤️ by the AI VR Tour Guide team**

*Transforming education through immersive AI-powered experiences*
