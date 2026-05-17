# SAGE Architecture Documentation

This document provides a comprehensive overview of the SAGE (Semantic Academic Graph Explorer) system architecture, design decisions, and technical implementation details.

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Decisions](#design-decisions)
7. [Integration Points](#integration-points)
8. [Performance Considerations](#performance-considerations)
9. [Security Architecture](#security-architecture)

---

## System Overview

SAGE is a full-stack research assistant application built with a modern microservices-inspired architecture. The system consists of three main layers:

1. **Frontend Layer**: Next.js 14 application with React components
2. **Backend Layer**: FastAPI REST API with WebSocket support
3. **Integration Layer**: MCP (Model Context Protocol) servers for external APIs

### Key Characteristics
- **Asynchronous**: All I/O operations are async for maximum throughput
- **Real-time**: WebSocket-based streaming for live updates
- **Modular**: Clean separation of concerns with pluggable components
- **Resilient**: Comprehensive error handling and retry logic
- **Testable**: >80% code coverage with extensive mocking

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Query      │  │   Results    │  │     Chat     │        │
│  │   Section    │  │     Tabs     │  │    Drawer    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                  │                  │                │
│         └──────────────────┴──────────────────┘                │
│                            │                                    │
│                    ┌───────▼────────┐                          │
│                    │  Next.js API   │                          │
│                    │    Routes      │                          │
│                    └───────┬────────┘                          │
└────────────────────────────┼───────────────────────────────────┘
                             │ HTTP/WebSocket
┌────────────────────────────▼───────────────────────────────────┐
│                         BACKEND LAYER                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                   │  │
│  │                                                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │  │
│  │  │  Query   │  │ Analyze  │  │ Proposal │  │   Chat  │ │  │
│  │  │  Routes  │  │  Routes  │  │  Routes  │  │   WS    │ │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │  │
│  └───────┼─────────────┼─────────────┼─────────────┼──────┘  │
│          │             │             │             │          │
│  ┌───────▼─────────────▼─────────────▼─────────────▼──────┐  │
│  │              Pipeline Orchestrator                      │  │
│  │         (Skill-based processing engine)                 │  │
│  └───────┬─────────────┬─────────────┬─────────────┬──────┘  │
│          │             │             │             │          │
│  ┌───────▼──────┐ ┌────▼─────┐ ┌────▼─────┐ ┌────▼─────┐   │
│  │  Citation    │ │ Timeline │ │  Skills  │ │  Models  │   │
│  │   Graph      │ │  Engine  │ │  (YAML)  │ │ (Pydantic)│  │
│  │   Engine     │ │          │ │          │ │          │   │
│  └──────────────┘ └──────────┘ └──────────┘ └──────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│                      INTEGRATION LAYER                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Semantic   │  │    arXiv     │  │   DeepL      │        │
│  │   Scholar    │  │     MCP      │  │    MCP       │        │
│  │     MCP      │  │              │  │              │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                  │                │
└─────────┼─────────────────┼──────────────────┼────────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ Semantic │      │  arXiv   │      │  DeepL   │
    │ Scholar  │      │   API    │      │   API    │
    │   API    │      │          │      │          │
    └──────────┘      └──────────┘      └──────────┘
```

---

## Component Details

### Frontend Components

#### 1. QuerySection.tsx
**Purpose**: User input interface for research queries

**Key Features**:
- Query text input with validation
- Advanced filters (year range, categories)
- Max results configuration
- Real-time validation feedback

**State Management**:
- Local state for form inputs
- Debounced query submission
- Loading states during API calls

#### 2. ResultsTabs.tsx
**Purpose**: Display analysis results in organized tabs

**Tabs**:
- **Papers**: List of retrieved papers with metadata
- **Graph**: Interactive citation network visualization (vis.js)
- **Timeline**: Temporal trends chart (Chart.js)
- **Summary**: AI-generated synthesis

**Data Flow**:
- Receives data from parent via props
- Manages active tab state
- Lazy loads heavy visualizations

#### 3. ChatDrawer.tsx
**Purpose**: Real-time chat interface with AI assistant

**Features**:
- WebSocket connection management
- Message history with auto-scroll
- Typing indicators
- Error recovery

**WebSocket Protocol**:
```typescript
// Client → Server
{
  type: "message",
  content: "user query"
}

// Server → Client
{
  type: "assistant",
  content: "AI response",
  metadata: { ... }
}
```

#### 4. RealtimePipeline.tsx
**Purpose**: Live progress tracking for analysis pipeline

**Features**:
- Step-by-step progress visualization
- Real-time status updates via WebSocket
- Error state handling
- Completion notifications

### Backend Components

#### 1. API Routes

**Query Route** (`/api/query`)
```python
@router.post("/query")
async def start_query(payload: PaperQueryRequest) -> dict:
    """
    Initiates paper search and analysis pipeline.
    
    Flow:
    1. Validate input
    2. Create session
    3. Start background pipeline
    4. Return session ID + WebSocket URL
    """
```

**Analyze Route** (`/api/analyze`)
```python
@router.post("/analyze")
async def analyze_papers(payload: AnalyzeRequest) -> dict:
    """
    Analyzes existing paper set.
    
    Operations:
    - Build citation graph
    - Generate timeline
    - Compute statistics
    """
```

**Proposal Route** (`/api/proposal`)
```python
@router.post("/proposal")
async def generate_proposal(payload: ProposalRequest) -> dict:
    """
    Generates research proposal from papers.
    
    Output:
    - LaTeX document
    - Bibliography
    - Structured sections
    """
```

#### 2. Engines

**Citation Graph Engine** (`citation_graph.py`)

**Core Algorithm**:
```python
def build_citation_graph(papers, citations):
    """
    1. Create directed graph (NetworkX)
    2. Add nodes with metadata
    3. Add edges (citing → cited)
    4. Compute PageRank (α=0.85)
    5. Scale node sizes by influence
    6. Export to vis.js format
    
    Complexity: O(n + m) construction, O(n*m) PageRank
    """
```

**Key Functions**:
- `build_citation_graph()`: Main graph construction
- `get_graph_summary()`: Statistical analysis
- PageRank computation with fallback for disconnected graphs

**Timeline Engine** (`timeline.py`)

**Core Algorithm**:
```python
def build_timeline(papers, citations):
    """
    1. Aggregate papers by year
    2. Attribute citations to cited paper's year
    3. Fill gaps (min_year to max_year)
    4. Return continuous timeline
    
    Complexity: O(n + m)
    """
```

**Key Functions**:
- `build_timeline()`: Year-by-year aggregation
- `detect_paradigm_shifts()`: Growth rate analysis (>100% YoY)
- `get_timeline_summary()`: CAGR and statistics

#### 3. MCP Servers

**Semantic Scholar MCP** (`semantic_scholar_mcp.py`)

**Features**:
- Rate limiting (1 RPS)
- Exponential backoff on 429
- API key support (optional)
- Fallback to arXiv-only mode

**Rate Limiter**:
```python
async def _respect_rate_limit():
    """
    Enforces 1 RPS across all S2 calls.
    Uses monotonic clock for accuracy.
    """
    global _last_call_ts
    elapsed = time.monotonic() - _last_call_ts
    if elapsed < 1.05:  # 1.05s = 1 RPS with buffer
        await asyncio.sleep(1.05 - elapsed)
    _last_call_ts = time.monotonic()
```

**arXiv MCP** (`arxiv_mcp.py`)

**Features**:
- XML parsing (Atom format)
- Year filtering (post-fetch)
- Category filtering
- Retry on 429

**XML Parsing**:
```python
def _parse_arxiv_response(xml_text):
    """
    Parses Atom XML from arXiv API.
    
    Extracts:
    - Paper ID, title, abstract
    - Authors, categories
    - Publication date → year
    - DOI, journal reference
    """
```

**Translation MCP** (`translation_mcp.py`)

**Status**: Placeholder for future DeepL integration

**Planned Features**:
- Abstract translation
- Query translation
- Multi-language support

#### 4. Skills (YAML-based)

**Extraction Skill** (`extraction_skill.yaml`)
- Extracts key information from papers
- Identifies research gaps
- Summarizes methodologies

**Synthesis Skill** (`synthesis_skill.yaml`)
- Generates literature reviews
- Identifies trends and patterns
- Creates coherent narratives

**Graph Skill** (`graph_skill.yaml`)
- Analyzes citation patterns
- Identifies influential papers
- Detects research communities

**Translation Skill** (`translation_skill.yaml`)
- Translates abstracts
- Handles technical terminology
- Preserves scientific accuracy

**Proposal Skill** (`proposal_skill.yaml`)
- Generates research proposals
- Creates LaTeX documents
- Structures sections (intro, methods, etc.)

---

## Data Flow

### Query Pipeline

```
User Input
    │
    ▼
Frontend Validation
    │
    ▼
POST /api/query
    │
    ▼
Create Session
    │
    ▼
Background Pipeline Start
    │
    ├─► Search Papers (S2/arXiv)
    │       │
    │       ▼
    │   Fetch Citations
    │       │
    │       ▼
    │   Build Citation Graph
    │       │
    │       ▼
    │   Build Timeline
    │       │
    │       ▼
    │   AI Synthesis
    │       │
    │       ▼
    │   Store Results
    │
    ▼
Return Session ID + WS URL
    │
    ▼
Frontend Connects to WebSocket
    │
    ▼
Real-time Progress Updates
    │
    ▼
Display Results
```

### WebSocket Communication

```
Client                          Server
  │                               │
  ├─── Connect ──────────────────►│
  │                               │
  │◄──── Connected ───────────────┤
  │                               │
  ├─── Message ───────────────────►│
  │                               │
  │                          Process
  │                               │
  │◄──── Streaming Response ──────┤
  │◄──── Streaming Response ──────┤
  │◄──── Streaming Response ──────┤
  │                               │
  │◄──── Complete ────────────────┤
  │                               │
  ├─── Disconnect ────────────────►│
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **Async Runtime**: asyncio + uvicorn
- **Data Validation**: Pydantic v2
- **Graph Library**: NetworkX 3.2+
- **HTTP Client**: httpx (async)
- **Testing**: pytest + pytest-asyncio + pytest-mock

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5+
- **UI Library**: React 18
- **Styling**: Tailwind CSS
- **Visualization**: vis.js (graphs), Chart.js (timelines)
- **WebSocket**: Native WebSocket API

### External APIs
- **Semantic Scholar**: Graph API v1
- **arXiv**: Export API (Atom XML)
- **DeepL**: Translation API v2 (planned)
- **Anthropic Claude**: Via MCP (planned)

### Infrastructure
- **Development**: uvicorn (ASGI server)
- **Production**: Gunicorn + uvicorn workers
- **Deployment**: Vercel (frontend), Railway/Fly.io (backend)

---

## Design Decisions

### 1. Why FastAPI?
**Decision**: Use FastAPI over Flask/Django

**Rationale**:
- Native async/await support (critical for I/O-heavy operations)
- Automatic OpenAPI documentation
- Pydantic integration for type safety
- WebSocket support out of the box
- High performance (comparable to Node.js)

### 2. Why NetworkX?
**Decision**: Use NetworkX for graph algorithms

**Rationale**:
- Mature, well-tested library
- Rich algorithm library (PageRank, clustering, etc.)
- Good performance for graphs <10K nodes
- Pythonic API
- Extensive documentation

**Alternative Considered**: igraph (faster but less Pythonic)

### 3. Why Skill-based Architecture?
**Decision**: Use YAML skill definitions instead of hardcoded prompts

**Rationale**:
- Separation of concerns (logic vs. prompts)
- Easy to modify without code changes
- Version control for prompts
- A/B testing capabilities
- Non-technical users can edit

### 4. Why MCP Servers?
**Decision**: Wrap external APIs in MCP server pattern

**Rationale**:
- Consistent interface across APIs
- Centralized rate limiting
- Easy to mock for testing
- Pluggable architecture
- Future-proof for MCP protocol adoption

### 5. Why WebSocket for Chat?
**Decision**: Use WebSocket instead of Server-Sent Events (SSE)

**Rationale**:
- Bidirectional communication
- Lower latency
- Better browser support
- Simpler protocol
- Native support in FastAPI

**Trade-off**: More complex than REST, but necessary for real-time features

### 6. Why Synthetic Citations?
**Decision**: Generate synthetic citations when S2 API unavailable

**Rationale**:
- Graceful degradation
- Demo-friendly (works without API keys)
- Reasonable approximation based on:
  - Temporal ordering (newer cites older)
  - Category similarity
  - Weighted random selection

**Limitation**: Not real citation data, but useful for visualization

---

## Integration Points

### Semantic Scholar API

**Endpoint**: `https://api.semanticscholar.org/graph/v1`

**Rate Limits**:
- Without key: 1 request/second
- With key: 10 requests/second

**Key Endpoints**:
- `/paper/search`: Search papers
- `/paper/{id}`: Get paper details
- `/paper/{id}/citations`: Get citations

**Error Handling**:
- 429: Exponential backoff (2s, 4s, 6s)
- 503: Retry with backoff
- Timeout: 15s, then retry

### arXiv API

**Endpoint**: `https://export.arxiv.org/api/query`

**Rate Limits**:
- 1 request per 3 seconds (recommended)
- SAGE uses 5s delay for safety

**Query Format**:
```
?search_query=all:CRISPR+AND+cat:q-bio.GN
&start=0
&max_results=50
&sortBy=relevance
```

**Response Format**: Atom XML

**Error Handling**:
- 429: Retry with 5s, 10s, 15s delays
- Parse errors: Skip malformed entries

### DeepL API (Planned)

**Endpoint**: `https://api-free.deepl.com/v2/translate`

**Rate Limits**:
- Free: 500,000 chars/month
- Pro: Custom limits

**Use Cases**:
- Translate abstracts to English
- Translate user queries
- Multi-language support

---

## Performance Considerations

### Backend Optimization

**1. Async I/O**
- All external API calls are async
- Concurrent requests where possible
- Connection pooling with httpx

**2. Rate Limiting**
- Enforced at MCP server level
- Prevents API bans
- Configurable per service

**3. Caching Strategy**
- Session-based caching (in-memory)
- Paper metadata cached per session
- No persistent cache (stateless design)

**4. Graph Algorithms**
- PageRank: O(n*m) but converges quickly (~100 iterations)
- Timeline: O(n + m) linear time
- Optimized for typical query size (50-200 papers)

### Frontend Optimization

**1. Code Splitting**
- Next.js automatic code splitting
- Lazy load heavy components (vis.js)
- Dynamic imports for visualizations

**2. Data Fetching**
- SWR for client-side caching
- Optimistic updates
- Stale-while-revalidate pattern

**3. Rendering**
- React Server Components where possible
- Memoization for expensive computations
- Virtual scrolling for large lists

### Scalability

**Current Limits**:
- 50-200 papers per query (optimal)
- 1-10 concurrent users (single instance)
- ~5-15 seconds per query

**Scaling Strategy**:
- Horizontal scaling (multiple backend instances)
- Load balancer for WebSocket connections
- Redis for session storage (future)
- CDN for frontend assets

---

## Security Architecture

### Input Validation
- Pydantic models for all inputs
- Type checking at runtime
- SQL injection: N/A (no database)
- XSS: Sanitized in frontend

### API Security
- CORS configured for allowed origins
- Rate limiting per IP (future)
- API key validation
- No sensitive data in logs

### Data Privacy
- No persistent storage of user data
- Session data cleared after completion
- API keys stored in environment variables
- No PII collected

### Audit Trail
- All operations logged
- Timestamps and session IDs
- Error tracking
- Performance metrics

See [docs/SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md) for detailed security review.

---

## Future Enhancements

### Planned Features
1. **Persistent Storage**: PostgreSQL for user accounts and saved queries
2. **Authentication**: JWT-based auth with OAuth providers
3. **Caching Layer**: Redis for API response caching
4. **Advanced Visualizations**: 3D graphs, heatmaps, network motifs
5. **PDF Parsing**: Full-text analysis with PyMuPDF
6. **Recommendation Engine**: Collaborative filtering for paper suggestions
7. **Export Formats**: Zotero, Mendeley, BibTeX
8. **Mobile App**: React Native version

### Architecture Evolution
- Microservices: Split into separate services (search, analysis, chat)
- Message Queue: RabbitMQ/Kafka for async processing
- Container Orchestration: Kubernetes for production
- Monitoring: Prometheus + Grafana
- Logging: ELK stack

---

## Conclusion

SAGE's architecture is designed for:
- **Modularity**: Easy to extend and modify
- **Resilience**: Graceful degradation and error recovery
- **Performance**: Async I/O and optimized algorithms
- **Maintainability**: Clean code, comprehensive tests, clear documentation

The system successfully balances complexity and simplicity, providing a robust foundation for academic research assistance.

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Maintained By**: SAGE Development Team  
**Made with Bob**