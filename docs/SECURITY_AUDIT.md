# SAGE Security Audit Report

**Date:** May 17, 2026  
**Auditor:** IBM Bob  
**Scope:** Backend codebase security review  
**Version:** 1.0

---

## Executive Overview

The SAGE backend demonstrates **good foundational security practices** with proper environment variable handling and API key protection. However, several **medium to high priority vulnerabilities** require attention, particularly around input validation, CORS configuration, session management, and error handling.

**Overall Security Posture:** 🟡 **MODERATE** - Production-ready with recommended fixes

**Key Strengths:**
- ✅ API keys properly externalized via `.env`
- ✅ `.env` correctly gitignored
- ✅ Rate limiting implemented for external APIs
- ✅ Pydantic models provide basic type validation

**Critical Gaps:**
- ❌ No input sanitization or length limits
- ❌ Overly permissive CORS configuration
- ❌ No session expiration or cleanup mechanism
- ❌ Error messages may leak sensitive information
- ❌ No authentication/authorization layer

---

## Findings

### 🔴 Critical Issues

#### 1. **No Authentication/Authorization Layer**
**Location:** All API routes  
**Risk:** Anyone can access all endpoints without authentication

**Details:**
- All routes in `backend/api/routes/` are completely open
- No API key validation for client requests
- No rate limiting on client requests (only on external APIs)
- Session IDs are UUIDs but not validated against any user identity

**Impact:** 
- Unauthorized access to all functionality
- Potential for abuse and resource exhaustion
- No audit trail of who performed actions

**Recommendation:**
```python
# Add API key middleware or JWT authentication
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.client_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

---

### 🟠 High Priority

#### 2. **Overly Permissive CORS Configuration**
**Location:** `backend/main.py:10-16`  
**Risk:** Allows all HTTP methods and headers from configured origins

**Current Configuration:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # ⚠️ Too permissive
    allow_headers=["*"],  # ⚠️ Too permissive
)
```

**Issues:**
- `allow_methods=["*"]` permits all HTTP methods including dangerous ones (PUT, DELETE, PATCH)
- `allow_headers=["*"]` allows any custom headers
- `allow_credentials=True` with wildcards can be exploited

**Recommendation:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only needed methods
    allow_headers=["Content-Type", "Authorization"],  # Specific headers
    max_age=3600,  # Cache preflight requests
)
```

#### 3. **No Input Validation or Sanitization**
**Location:** All API routes  
**Risk:** Potential for injection attacks and resource exhaustion

**Vulnerable Areas:**

**a) Query String Injection (`query.py:11`, `websocket.py:135`)**
```python
# No length limit or sanitization
payload.query  # Could be 10MB of text
query = data.get("query", "")  # No validation
```

**b) Session ID Validation (`pipeline.py:11`)**
```python
# No format validation - accepts any string
session = get_session(session_id)
```

**c) Pydantic Models Lack Constraints (`models/paper.py`)**
```python
class PaperQueryRequest(BaseModel):
    query: str  # No max length
    max_papers: int = 50  # No upper bound validation
    disciplines: list[str] = []  # No length limit
```

**Recommendation:**
```python
from pydantic import Field, validator
import re

class PaperQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    max_papers: int = Field(default=50, ge=1, le=100)
    disciplines: list[str] = Field(default=[], max_items=10)
    
    @validator('query')
    def sanitize_query(cls, v):
        # Remove control characters
        return re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
    
    @validator('disciplines')
    def validate_disciplines(cls, v):
        # Whitelist allowed disciplines
        allowed = {'cs', 'physics', 'math', 'bio', 'chem'}
        return [d for d in v if d.lower() in allowed]
```

#### 4. **Session Store Lacks Security Controls**
**Location:** `backend/pipeline_store.py`  
**Risk:** Memory exhaustion, session hijacking, data leakage

**Issues:**
- No session expiration mechanism
- No maximum session limit (unbounded memory growth)
- No session cleanup on completion
- Session data persists indefinitely in memory
- No validation that session_id is a valid UUID format

**Current Implementation:**
```python
_sessions: dict[str, dict[str, Any]] = {}  # Grows forever

def create_session(session_id: str, query: str):
    # No expiration, no limit check
    _sessions[session_id] = {...}
```

**Recommendation:**
```python
import time
from collections import OrderedDict

MAX_SESSIONS = 1000
SESSION_TTL = 3600  # 1 hour

_sessions: OrderedDict[str, dict[str, Any]] = OrderedDict()

def _cleanup_expired_sessions():
    """Remove sessions older than TTL."""
    now = time.time()
    expired = [
        sid for sid, sess in _sessions.items()
        if now - sess.get("created_at", 0) > SESSION_TTL
    ]
    for sid in expired:
        del _sessions[sid]

def create_session(session_id: str, query: str):
    _cleanup_expired_sessions()
    
    # Enforce session limit (FIFO eviction)
    if len(_sessions) >= MAX_SESSIONS:
        _sessions.popitem(last=False)
    
    # Validate UUID format
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise ValueError("Invalid session ID format")
    
    _sessions[session_id] = {...}
```

#### 5. **Error Messages May Leak Sensitive Information**
**Location:** `websocket.py:116-121`, `pipeline_store.py:118-119`  
**Risk:** Information disclosure through error messages

**Current Implementation:**
```python
except Exception as e:
    await websocket.send_json({
        "stage": "error",
        "message": str(e),  # ⚠️ May expose internal details
    })
```

**Issues:**
- Raw exception messages sent to client
- May expose file paths, API keys, internal structure
- Stack traces not logged for debugging

**Recommendation:**
```python
import logging

logger = logging.getLogger(__name__)

except Exception as e:
    # Log full error internally
    logger.error(f"Pipeline error for session {session_id}: {e}", exc_info=True)
    
    # Send generic message to client
    await websocket.send_json({
        "stage": "error",
        "message": "An error occurred processing your request",
        "error_code": "PIPELINE_ERROR",
    })
```

---

### 🟡 Medium Priority

#### 6. **API Keys in Headers Without Encryption**
**Location:** `semantic_scholar_mcp.py:42-43`  
**Risk:** API keys transmitted in plaintext (mitigated by HTTPS)

**Current Implementation:**
```python
headers = {}
if settings.semantic_scholar_api_key:
    headers["x-api-key"] = settings.semantic_scholar_api_key
```

**Note:** This is acceptable if HTTPS is enforced. Verify production deployment uses HTTPS.

**Recommendation:**
- Ensure FastAPI app runs behind HTTPS in production
- Add HSTS headers
- Consider using environment-specific API keys (dev/staging/prod)

#### 7. **No Rate Limiting on Client Requests**
**Location:** All API routes  
**Risk:** Resource exhaustion from malicious or buggy clients

**Current State:**
- Rate limiting only on external APIs (arXiv, Semantic Scholar)
- No limits on client requests to SAGE endpoints
- Single client could spawn unlimited sessions

**Recommendation:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/query")
@limiter.limit("10/minute")  # 10 queries per minute per IP
async def start_query(request: Request, payload: PaperQueryRequest):
    ...
```

#### 8. **Hardcoded WebSocket URL in Response**
**Location:** `query.py:19`  
**Risk:** Breaks in different deployment environments

```python
"websocket_url": f"ws://localhost:8000/api/chat/{session_id}",  # ⚠️ Hardcoded
```

**Recommendation:**
```python
# In config.py
class Settings(BaseSettings):
    websocket_base_url: str = "ws://localhost:8000"
    
# In query.py
"websocket_url": f"{settings.websocket_base_url}/api/chat/{session_id}",
```

#### 9. **Empty Security Utilities**
**Location:** `backend/utils/audit_logger.py`, `backend/utils/validators.py`  
**Risk:** Missing security infrastructure

**Current State:**
- `audit_logger.py` is completely empty
- `validators.py` is completely empty
- No audit trail of actions
- No centralized validation logic

**Recommendation:**
Implement audit logging:
```python
# audit_logger.py
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("sage.audit")

def log_query(session_id: str, query: str, ip_address: str):
    logger.info(f"QUERY | {session_id} | {ip_address} | {query[:100]}")

def log_error(session_id: str, error: str, context: dict[str, Any]):
    logger.error(f"ERROR | {session_id} | {error} | {context}")
```

#### 10. **No Request Size Limits**
**Location:** FastAPI app configuration  
**Risk:** Large payload DoS attacks

**Current State:**
- No max request body size configured
- Could accept multi-GB JSON payloads

**Recommendation:**
```python
# In main.py
app = FastAPI(
    title="SAGE Backend",
    max_request_size=1_000_000,  # 1MB limit
)
```

---

### 🟢 Low Priority

#### 11. **Missing Security Headers**
**Location:** `main.py`  
**Risk:** Browser-based attacks (XSS, clickjacking)

**Recommendation:**
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "*.vercel.app"])
```

#### 12. **Synthetic Citation Generation Uses Weak Randomness**
**Location:** `semantic_scholar_mcp.py:160-199`  
**Risk:** Predictable synthetic data (low impact for research tool)

**Current Implementation:**
```python
import random  # Uses Mersenne Twister (not cryptographically secure)
```

**Note:** This is acceptable for synthetic research data. Only a concern if used for security-sensitive operations.

#### 13. **No Logging Configuration**
**Location:** Entire codebase  
**Risk:** Difficult to debug issues in production

**Recommendation:**
```python
# In main.py or separate logging_config.py
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/sage.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

---

## Recommendations

### Immediate Actions (Week 1)

1. **Add Input Validation** - Implement Pydantic field constraints and validators
2. **Restrict CORS** - Limit allowed methods and headers
3. **Implement Session Expiration** - Add TTL and cleanup mechanism
4. **Sanitize Error Messages** - Remove sensitive details from client responses
5. **Add Request Rate Limiting** - Protect against abuse

### Short-term (Sprint 1-2)

6. **Implement Authentication** - Add API key or JWT-based auth
7. **Add Security Headers** - Implement security middleware
8. **Configure Logging** - Set up structured logging with rotation
9. **Add Audit Trail** - Implement audit_logger.py
10. **Validate Session IDs** - Ensure UUID format validation

### Medium-term (Next Quarter)

11. **Add Request Size Limits** - Configure max payload sizes
12. **Implement HTTPS Enforcement** - Add redirect middleware
13. **Add Health Check Security** - Protect /health endpoint
14. **Implement Session Encryption** - Encrypt sensitive session data
15. **Add Monitoring & Alerting** - Track security events

---

## Quick-Fix Checklist

### Configuration & Environment
- [x] `.env` is gitignored
- [x] `.env.example` provided with placeholder values
- [ ] Add `.env.production` template with production-specific settings
- [ ] Document required environment variables in README
- [ ] Add environment variable validation on startup

### API Security
- [ ] Add authentication middleware (API key or JWT)
- [ ] Implement rate limiting on all client-facing endpoints
- [ ] Add request size limits (1MB default)
- [ ] Restrict CORS to specific methods: `["GET", "POST"]`
- [ ] Restrict CORS to specific headers: `["Content-Type", "Authorization"]`
- [ ] Add security headers middleware

### Input Validation
- [ ] Add `max_length` constraints to all string fields
- [ ] Add `ge`/`le` constraints to all numeric fields
- [ ] Add `max_items` constraints to all list fields
- [ ] Implement query sanitization (remove control characters)
- [ ] Validate session_id format (UUID)
- [ ] Whitelist allowed disciplines/categories

### Session Management
- [ ] Implement session TTL (1 hour default)
- [ ] Add session cleanup mechanism
- [ ] Enforce maximum session limit (1000 default)
- [ ] Add session validation on retrieval
- [ ] Consider Redis for production session storage

### Error Handling
- [ ] Sanitize all error messages sent to clients
- [ ] Log full errors internally with context
- [ ] Use error codes instead of raw messages
- [ ] Implement custom exception handlers
- [ ] Add error monitoring/alerting

### Logging & Monitoring
- [ ] Implement audit_logger.py with structured logging
- [ ] Configure log rotation (10MB, 5 backups)
- [ ] Log all authentication attempts
- [ ] Log all query submissions with IP
- [ ] Log all errors with full context
- [ ] Add performance metrics logging

### External API Security
- [x] Rate limiting implemented for Semantic Scholar (1 RPS)
- [x] Rate limiting implemented for arXiv (3s delay)
- [x] Retry logic with exponential backoff
- [ ] Add timeout configuration to settings
- [ ] Implement circuit breaker pattern
- [ ] Add API key rotation mechanism

### Production Readiness
- [ ] Ensure HTTPS enforcement in production
- [ ] Add HSTS headers
- [ ] Configure trusted host middleware
- [ ] Add health check authentication
- [ ] Implement graceful shutdown
- [ ] Add startup validation checks
- [ ] Document security configuration

---

## Security Testing Recommendations

### Manual Testing
1. **Test with malicious inputs:**
   - Very long query strings (>10KB)
   - Special characters and control codes
   - SQL injection patterns (if DB added later)
   - XSS payloads in query strings

2. **Test session management:**
   - Create 1000+ sessions rapidly
   - Try to access other users' sessions
   - Test session expiration behavior

3. **Test rate limiting:**
   - Send 100 requests in 1 second
   - Verify 429 responses

### Automated Testing
```python
# tests/test_security.py
import pytest
from fastapi.testclient import TestClient

def test_query_length_limit():
    """Test that overly long queries are rejected."""
    client = TestClient(app)
    long_query = "a" * 10000
    response = client.post("/api/query", json={"query": long_query})
    assert response.status_code == 422

def test_invalid_session_id():
    """Test that invalid session IDs are rejected."""
    client = TestClient(app)
    response = client.get("/api/pipeline/not-a-uuid")
    assert response.status_code == 400

def test_cors_headers():
    """Test that CORS headers are properly restricted."""
    client = TestClient(app)
    response = client.options("/api/query")
    assert "DELETE" not in response.headers.get("Access-Control-Allow-Methods", "")
```

---

## Compliance Notes

### GDPR Considerations
- No personal data currently collected
- Session IDs are anonymous UUIDs
- If user accounts added: implement data retention policies

### API Key Management
- Keys stored in environment variables ✅
- Keys not logged or exposed ✅
- Consider key rotation policy for production

### Data Retention
- In-memory sessions have no persistence ✅
- Consider adding session data retention policy
- Document what data is stored and for how long

---

## Conclusion

The SAGE backend has a **solid security foundation** with proper API key management and rate limiting for external services. However, **production deployment requires addressing the high-priority issues**, particularly:

1. Adding authentication/authorization
2. Implementing comprehensive input validation
3. Restricting CORS configuration
4. Adding session expiration and cleanup
5. Sanitizing error messages

With these fixes implemented, SAGE will have **production-grade security** suitable for public deployment.

**Estimated Effort:** 2-3 developer days for high-priority fixes

---

**Report End**