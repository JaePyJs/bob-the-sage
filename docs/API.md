# SAGE API Reference

Complete API documentation for the SAGE (Semantic Academic Graph Explorer) backend.

**Base URL**: `http://localhost:8000`  
**API Version**: 1.0  
**Protocol**: HTTP/1.1, WebSocket

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health Check](#health-check)
3. [Query Endpoints](#query-endpoints)
4. [Analysis Endpoints](#analysis-endpoints)
5. [Proposal Endpoints](#proposal-endpoints)
6. [Pipeline Endpoints](#pipeline-endpoints)
7. [WebSocket Protocol](#websocket-protocol)
8. [Error Handling](#error-handling)
9. [Rate Limits](#rate-limits)
10. [Data Models](#data-models)

---

## Authentication

**Current Status**: No authentication required (v1.0)

**Future**: JWT-based authentication planned for v2.0

```http
Authorization: Bearer <token>
```

---

## Health Check

### GET /health

Check if the API is running and healthy.

**Request**:
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response** (200 OK):
```json
{
  "status": "ok",
  "service": "sage-backend"
}
```

**Use Cases**:
- Monitoring and health checks
- Load balancer health probes
- Smoke tests

---

## Query Endpoints

### POST /api/query

Start a new paper search and analysis pipeline.

**Request**:
```http
POST /api/query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "CRISPR gene editing",
  "max_results": 50,
  "year_from": 2015,
  "year_to": 2024,
  "categories": ["q-bio.GN", "q-bio.MN"]
}
```

**Request Body**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Search query (keywords, phrases) |
| `max_results` | integer | No | Max papers to retrieve (default: 50, max: 200) |
| `year_from` | integer | No | Start year filter (e.g., 2015) |
| `year_to` | integer | No | End year filter (e.g., 2024) |
| `categories` | array[string] | No | arXiv categories (e.g., ["cs.AI", "cs.LG"]) |

**Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "websocket_url": "ws://localhost:8000/api/chat/550e8400-e29b-41d4-a716-446655440000"
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string (UUID) | Unique session identifier |
| `status` | string | Pipeline status ("processing", "completed", "error") |
| `websocket_url` | string | WebSocket URL for real-time updates |

**Error Responses**:

**400 Bad Request** - Invalid input:
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Example Usage**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "query": "machine learning protein folding",
        "max_results": 30,
        "year_from": 2020
    }
)

session_id = response.json()["session_id"]
print(f"Session started: {session_id}")
```

---

## Analysis Endpoints

### POST /api/analyze

Analyze a set of papers (citation graph, timeline, statistics).

**Request**:
```http
POST /api/analyze HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "papers": [
    {
      "paper_id": "p1",
      "title": "CRISPR-Cas9 Gene Editing",
      "authors": ["Jennifer Doudna"],
      "year": 2012,
      "abstract": "...",
      "primary_category": "q-bio.GN"
    }
  ],
  "citations": [
    {
      "citing_id": "p2",
      "cited_id": "p1",
      "weight": 1.0
    }
  ]
}
```

**Request Body**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `papers` | array[Paper] | Yes | List of paper objects |
| `citations` | array[Citation] | No | List of citation edges |

**Paper Object**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `paper_id` | string | Yes | Unique paper identifier |
| `title` | string | No | Paper title |
| `authors` | array[string] | No | Author names |
| `year` | integer | No | Publication year |
| `abstract` | string | No | Paper abstract |
| `primary_category` | string | No | Primary category/field |

**Citation Object**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `citing_id` | string | Yes | ID of citing paper |
| `cited_id` | string | Yes | ID of cited paper |
| `weight` | float | No | Citation weight (0.0-1.0, default: 0.5) |

**Response** (200 OK):
```json
{
  "graph": {
    "nodes": [
      {
        "id": "p1",
        "label": "CRISPR-Cas9 Gene Editing",
        "group": "q-bio.GN",
        "value": 5
      }
    ],
    "edges": [
      {
        "from_id": "p2",
        "to_id": "p1",
        "weight": 1.0
      }
    ]
  },
  "timeline": [
    {
      "year": "2012",
      "papers": 1,
      "citations": 0
    }
  ],
  "summary": {
    "total_papers": 1,
    "total_citations": 0,
    "year_range": ["2012", "2012"],
    "top_cited": [["p1", 0]]
  }
}
```

**Example Usage**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/analyze",
    json={
        "papers": papers_list,
        "citations": citations_list
    }
)

graph = response.json()["graph"]
print(f"Graph has {len(graph['nodes'])} nodes")
```

---

## Proposal Endpoints

### POST /api/proposal

Generate a research proposal from analyzed papers.

**Request**:
```http
POST /api/proposal HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "papers": [...],
  "topic": "CRISPR applications in medicine",
  "research_gap": "Limited clinical trials for rare diseases",
  "methodology": "Systematic review and meta-analysis"
}
```

**Request Body**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `papers` | array[Paper] | Yes | Papers to base proposal on |
| `topic` | string | Yes | Research topic/title |
| `research_gap` | string | No | Identified research gap |
| `methodology` | string | No | Proposed methodology |

**Response** (200 OK):
```json
{
  "proposal": {
    "title": "CRISPR Applications in Medicine: A Systematic Review",
    "abstract": "...",
    "introduction": "...",
    "literature_review": "...",
    "methodology": "...",
    "expected_outcomes": "...",
    "bibliography": "..."
  },
  "latex": "\\documentclass{article}\n...",
  "metadata": {
    "generated_at": "2024-01-15T10:30:00Z",
    "paper_count": 50,
    "word_count": 3500
  }
}
```

---

## Pipeline Endpoints

### GET /api/pipeline/{session_id}

Get the current status of a pipeline.

**Request**:
```http
GET /api/pipeline/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: localhost:8000
```

**Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "current_step": "synthesis",
  "results": {
    "papers": [...],
    "graph": {...},
    "timeline": [...],
    "summary": "..."
  },
  "created_at": "2024-01-15T10:25:00Z",
  "completed_at": "2024-01-15T10:25:15Z"
}
```

**Status Values**:
- `processing`: Pipeline is running
- `completed`: Pipeline finished successfully
- `error`: Pipeline encountered an error
- `cancelled`: Pipeline was cancelled by user

### DELETE /api/pipeline/{session_id}

Cancel a running pipeline.

**Request**:
```http
DELETE /api/pipeline/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: localhost:8000
```

**Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Pipeline cancelled successfully"
}
```

---

## WebSocket Protocol

### WS /api/chat/{session_id}

Real-time bidirectional communication for chat and pipeline updates.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/chat/session_id');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

### Message Types

#### Client → Server

**User Message**:
```json
{
  "type": "message",
  "content": "Explain CRISPR applications in medicine"
}
```

**Pipeline Control**:
```json
{
  "type": "control",
  "action": "pause"
}
```

#### Server → Client

**Assistant Response**:
```json
{
  "type": "assistant",
  "content": "CRISPR has several medical applications...",
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "model": "claude-3-opus"
  }
}
```

**Pipeline Progress**:
```json
{
  "type": "progress",
  "step": "searching",
  "progress": 25,
  "message": "Searching Semantic Scholar..."
}
```

**Pipeline Complete**:
```json
{
  "type": "complete",
  "results": {
    "papers": [...],
    "graph": {...},
    "timeline": [...]
  }
}
```

**Error**:
```json
{
  "type": "error",
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT_ERROR",
  "retry_after": 60
}
```

### Connection Lifecycle

```
Client                          Server
  │                               │
  ├─── Connect ──────────────────►│
  │                               │
  │◄──── Connected ───────────────┤
  │                               │
  ├─── Message ───────────────────►│
  │                               │
  │◄──── Response ────────────────┤
  │◄──── Response ────────────────┤
  │                               │
  ├─── Ping ──────────────────────►│
  │◄──── Pong ────────────────────┤
  │                               │
  ├─── Close ─────────────────────►│
  │◄──── Close ────────────────────┤
```

**Heartbeat**: Server sends ping every 30 seconds to keep connection alive.

---

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/query",
  "request_id": "req_123456"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Codes

| Code | Description | Action |
|------|-------------|--------|
| `VALIDATION_ERROR` | Input validation failed | Check request format |
| `RATE_LIMIT_ERROR` | Rate limit exceeded | Wait and retry |
| `API_ERROR` | External API error | Retry with backoff |
| `TIMEOUT_ERROR` | Request timeout | Retry request |
| `NOT_FOUND` | Resource not found | Check session ID |
| `INTERNAL_ERROR` | Server error | Contact support |

### Example Error Responses

**Validation Error (422)**:
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Rate Limit Error (429)**:
```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_ERROR",
  "retry_after": 60
}
```

**Not Found (404)**:
```json
{
  "detail": "Session not found",
  "error_code": "NOT_FOUND",
  "session_id": "invalid-id"
}
```

---

## Rate Limits

### API Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/query` | 10 requests | 1 minute |
| `/api/analyze` | 20 requests | 1 minute |
| `/api/proposal` | 5 requests | 1 minute |
| WebSocket | 1 connection | per session |

### External API Limits

| Service | Limit | Enforced By |
|---------|-------|-------------|
| Semantic Scholar | 1 req/sec | Backend |
| arXiv | 1 req/5 sec | Backend |
| DeepL | 500K chars/month | DeepL |

### Rate Limit Headers

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1642252800
```

---

## Data Models

### Paper Model

```typescript
interface Paper {
  paper_id: string;           // Unique identifier
  title: string;              // Paper title
  abstract?: string;          // Abstract text
  authors: string[];          // Author names
  year?: number;              // Publication year
  venue?: string;             // Publication venue
  doi?: string;               // DOI
  primary_category?: string;  // Primary category
  categories?: string[];      // All categories
  citation_count?: number;    // Citation count
  source: string;             // "semantic_scholar" | "arxiv"
}
```

### Citation Model

```typescript
interface Citation {
  citing_id: string;   // ID of citing paper
  cited_id: string;    // ID of cited paper
  weight?: number;     // Citation weight (0.0-1.0)
}
```

### Graph Model

```typescript
interface Graph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface GraphNode {
  id: string;          // Paper ID
  label: string;       // Display label
  group?: string;      // Category/group
  value?: number;      // Node size (PageRank-based)
}

interface GraphEdge {
  from_id: string;     // Source node ID
  to_id: string;       // Target node ID
  weight?: number;     // Edge weight
}
```

### Timeline Model

```typescript
interface TimelineEntry {
  year: string;        // Year as string
  papers: number;      // Paper count
  citations: number;   // Citation count
}
```

### Summary Model

```typescript
interface Summary {
  total_papers: number;
  total_citations: number;
  year_range: [string, string] | null;
  avg_papers_per_year: number;
  avg_citations_per_year: number;
  peak_year: string | null;
  peak_papers: number;
  growth_rate: number | null;
  top_cited: [string, number][];
}
```

---

## Examples

### Complete Query Flow

```python
import requests
import websocket
import json

# 1. Start query
response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "query": "CRISPR gene editing",
        "max_results": 50
    }
)

session_id = response.json()["session_id"]
ws_url = response.json()["websocket_url"]

# 2. Connect to WebSocket
def on_message(ws, message):
    data = json.loads(message)
    if data["type"] == "progress":
        print(f"Progress: {data['progress']}%")
    elif data["type"] == "complete":
        print("Analysis complete!")
        print(f"Found {len(data['results']['papers'])} papers")

ws = websocket.WebSocketApp(
    ws_url,
    on_message=on_message
)

ws.run_forever()
```

### Analyze Papers

```python
import requests

papers = [
    {
        "paper_id": "p1",
        "title": "CRISPR-Cas9",
        "year": 2012
    },
    {
        "paper_id": "p2",
        "title": "CRISPR Applications",
        "year": 2015
    }
]

citations = [
    {"citing_id": "p2", "cited_id": "p1"}
]

response = requests.post(
    "http://localhost:8000/api/analyze",
    json={
        "papers": papers,
        "citations": citations
    }
)

graph = response.json()["graph"]
timeline = response.json()["timeline"]
```

---

## Changelog

### v1.0 (2024-01-15)
- Initial API release
- Query, analyze, and proposal endpoints
- WebSocket support
- Citation graph and timeline analysis

### Planned (v2.0)
- Authentication (JWT)
- User accounts
- Saved queries
- Advanced filtering
- Batch operations

---

## Support

- **Documentation**: [https://sage-docs.example.com](https://sage-docs.example.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/sage/issues)
- **Email**: support@sage.example.com

---

**API Version**: 1.0  
**Last Updated**: 2024-01-15  
**Made with Bob**