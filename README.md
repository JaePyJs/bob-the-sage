# SAGE - Systematic Academic Guidance Engine

SAGE is an intelligent research assistant that transforms how researchers explore academic literature. By combining citation graph analysis, temporal trend detection, and AI-powered synthesis, SAGE helps researchers quickly understand research landscapes, identify influential papers, and generate comprehensive literature reviews.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.130-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![Test Coverage](https://img.shields.io/badge/coverage-90%25+-brightgreen.svg)](pytest.ini)

## Overview

Academic researchers face critical challenges: information overload from thousands of daily publications, complex citation analysis requirements, and time-consuming literature synthesis. SAGE addresses these through automated discovery, intelligent analysis, and AI-powered synthesis.

### Key Capabilities

- **Citation Graph Analysis**: NetworkX-based directed graphs with PageRank influence scoring (α=0.85)
- **Timeline Extraction**: Year-by-year aggregation with paradigm shift detection and CAGR calculation
- **Multi-Model AI Synthesis**: Orchestrated Claude, Gemini, and GPT-4 for comprehensive literature reviews
- **Real-Time Visualization**: Interactive graphs and timelines with live pipeline progress
- **Cross-Lingual Support**: Academic translation via DeepL integration

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/sage.git
cd sage
```

2. Set up backend
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env

# Configure API keys (obtain your own from providers)
# Edit .env and add:
# SEMANTIC_SCHOLAR_API_KEY=your_key_here
# DEEPL_API_KEY=your_key_here (optional)
```

3. Set up frontend
```bash
cd frontend
npm install
cd ..
```

### Running the Application

**Backend (Terminal 1)**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Frontend (Terminal 2)**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000` to access SAGE.

## API Documentation

### Core Endpoints

#### Health Check
```http
GET /health
```

Returns server status and configuration.

#### Query Papers
```http
POST /api/query
Content-Type: application/json

{
  "query": "machine learning",
  "max_results": 50,
  "year_from": 2020,
  "year_to": 2024
}
```

Initiates paper discovery and analysis pipeline. Returns session ID for tracking progress.

**Response**:
```json
{
  "session_id": "uuid-string",
  "status": "processing",
  "websocket_url": "ws://localhost:8000/api/chat/session_id"
}
```

#### Pipeline Status
```http
GET /api/pipeline/{session_id}
```

Polls pipeline progress and retrieves results.

**Response**:
```json
{
  "session_id": "uuid-string",
  "stage": "synthesis",
  "progress": 75,
  "papers_found": 30,
  "papers_analyzed": 30,
  "themes_identified": 5,
  "results": {
    "graph": {...},
    "timeline": {...},
    "synthesis": {...}
  }
}
```

#### WebSocket Chat
```http
WS /api/chat/{session_id}
```

Real-time bidirectional communication for interactive Q&A.

**Message Format**:
```json
{
  "type": "message",
  "content": "Explain CRISPR applications in gene therapy"
}
```

## Usage Examples

### Citation Graph Analysis

```python
from backend.engines.citation_graph import build_citation_graph, get_graph_summary

# Build graph with PageRank influence scoring
papers = [
    {"paper_id": "p1", "title": "Paper 1", "year": 2020},
    {"paper_id": "p2", "title": "Paper 2", "year": 2021}
]
citations = [
    {"citing_id": "p2", "cited_id": "p1", "weight": 0.8}
]

graph = build_citation_graph(papers, citations)
summary = get_graph_summary(papers, citations)

print(f"Total nodes: {summary['total_nodes']}")
print(f"Graph density: {summary['density']:.3f}")
print(f"Top cited papers: {summary['top_cited'][:3]}")
```

**Output**:
```
Total nodes: 2
Graph density: 0.500
Top cited papers: [{'paper_id': 'p1', 'title': 'Paper 1', 'citations': 1}]
```

### Timeline Analysis with Paradigm Shift Detection

```python
from backend.engines.timeline import build_timeline, detect_paradigm_shifts, get_timeline_summary

# Build timeline and detect shifts
timeline = build_timeline(papers, citations)
shifts = detect_paradigm_shifts(timeline, threshold=1.0, min_baseline=2)
summary = get_timeline_summary(timeline)

print(f"Year range: {summary['year_range']}")
print(f"CAGR: {summary['growth_rate']:.1f}%")
for shift in shifts:
    print(f"Paradigm shift in {shift['year']}: {shift['growth']:.0f}% growth")
```

**Output**:
```
Year range: 2020-2021
CAGR: 50.0%
Paradigm shift in 2021: 100% growth
```

### WebSocket Real-Time Chat

```javascript
const ws = new WebSocket('ws://localhost:8000/api/chat/session_id');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Assistant:', data.content);
};

ws.send(JSON.stringify({
  type: 'message',
  content: 'Explain CRISPR applications in gene therapy'
}));
```

## Architecture

SAGE follows a modular architecture with clear separation of concerns:

```
sage/
├── backend/                    # FastAPI backend
│   ├── api/                   # REST and WebSocket endpoints
│   │   └── routes/           # Query, pipeline, chat routes
│   ├── engines/               # Core analysis engines
│   │   ├── citation_graph.py # NetworkX + PageRank
│   │   └── timeline.py       # Temporal analysis + paradigm shifts
│   ├── mcp_servers/           # External API integrations
│   │   ├── semantic_scholar_mcp.py  # S2 API client
│   │   ├── arxiv_mcp.py             # arXiv API client
│   │   └── translation_mcp.py       # DeepL integration
│   ├── models/                # Pydantic data models
│   ├── skills/                # AI skill definitions (YAML)
│   ├── tests/                 # Comprehensive test suite (96 tests)
│   └── utils/                 # Logging, validation, audit
├── frontend/                   # Next.js 15 frontend
│   ├── app/components/        # React components
│   │   ├── QuerySection.tsx   # Search interface
│   │   ├── RealtimePipeline.tsx  # Progress visualization
│   │   ├── ResultsTabs.tsx    # Graph/timeline/synthesis display
│   │   └── ChatDrawer.tsx     # Interactive Q&A
│   └── app/api/               # API route handlers
├── .env.example               # Environment variable template
├── requirements.txt           # Python dependencies
└── pytest.ini                 # Test configuration
```

### Technology Stack

**Backend**:
- FastAPI 0.130 (async web framework)
- NetworkX 3.6 (graph algorithms)
- NumPy 2.2 / SciPy 1.15 (numerical computing)
- Pydantic 2.10 (data validation)
- httpx 0.28 (async HTTP client)

**Frontend**:
- Next.js 15 (React framework)
- TypeScript 5.x (type safety)
- Tailwind CSS (styling)

**Testing**:
- pytest 8.3 (test framework)
- pytest-asyncio 0.24 (async test support)
- pytest-cov (coverage reporting)

## Testing

SAGE includes a comprehensive test suite with 96 tests achieving 90%+ code coverage.

### Run All Tests
```bash
pytest backend/tests/ -v --cov=backend
```

### Run Specific Test Suite
```bash
pytest backend/tests/test_citation_graph.py -v
pytest backend/tests/test_timeline.py -v
pytest backend/tests/test_mcp_servers.py -v
```

### Generate Coverage Report
```bash
pytest backend/tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```

**Test Characteristics**:
- All tests use mocks (no live API calls)
- Fast execution (<1 minute for full suite)
- Comprehensive edge case coverage
- Async/await properly handled

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Literature API Keys (obtain your own from providers)
SEMANTIC_SCHOLAR_API_KEY=your_key_here
DEEPL_API_KEY=your_key_here

# CORS Configuration
ALLOWED_ORIGINS_RAW=http://localhost:3000

# Rate Limiting
ARXIV_DELAY_SECONDS=5
S2_REQUESTS_PER_SECOND=1
```

### Data Sources

SAGE integrates with external literature APIs. **API access requires your own credentials** from each provider:

- **Semantic Scholar**: Register at [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api)
- **arXiv**: No API key required, but rate limits apply
- **DeepL**: Optional, for translation features

**Important**: This repository does not include API keys. You must obtain and configure your own credentials. Comply with each provider's terms of service and rate limits.

### Alternative Data Sources

The architecture supports pluggable data sources:
- Internal institutional repositories
- Pre-curated research datasets
- Other academic APIs (PubMed, IEEE Xplore)
- Local PDF collections with metadata

## Performance

- **Citation Graph**: O(n + m) construction, O(n*m) PageRank convergence
- **Timeline**: O(n + m) aggregation with gap filling
- **API Rate Limits**: 
  - Semantic Scholar: 1 request/second (with exponential backoff)
  - arXiv: 1 request/5 seconds
- **Typical Query**: 5-15 seconds for 50 papers with full analysis

## Security

SAGE implements multiple security layers:

- **Input Validation**: Pydantic models validate all API inputs
- **Rate Limiting**: Enforced on all external API calls
- **CORS Protection**: Configurable allowed origins
- **Secret Management**: API keys externalized via environment variables
- **Error Handling**: No sensitive data in error responses or logs

## Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Write tests: Maintain >90% coverage
4. Follow code style: Use Black for Python, Prettier for TypeScript
5. Commit with conventional commits: `feat:`, `fix:`, `docs:`, `test:`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install pytest pytest-cov pytest-asyncio black

# Run linters
black backend/

# Run tests with coverage
pytest backend/tests/ --cov=backend
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Semantic Scholar** for academic paper data API
- **arXiv** for open access preprints
- **Anthropic Claude** for AI-powered synthesis
- **DeepL** for translation services
- **NetworkX** for graph algorithms
- **FastAPI** and **Next.js** for excellent frameworks

---

**SAGE** - Systematic Academic Guidance Engine  
*Intelligent research assistance through citation analysis and AI synthesis*