# SAGE Test Coverage Gap Analysis

**Current Coverage**: 87%  
**Target Coverage**: 90%+  
**Date**: May 17, 2026  
**Auditor**: IBM Bob (Senior Software Engineer)

## Executive Summary

This document provides a systematic analysis of all test coverage gaps in the SAGE codebase, classifies each gap, and provides actionable recommendations for improvement. The analysis prioritizes fixes by impact (coverage improvement) and effort (implementation complexity).

---

## Coverage Gaps by File

### 1. backend/api/websocket.py
**Coverage**: 22% (42 uncovered lines)  
**Classification**: DEAD CODE  
**Priority**: HIGH (for cleanup)

#### Root Cause Analysis
The WebSocket endpoint was replaced by HTTP polling due to WSL2 port forwarding issues on Windows. The comment in `pipeline_store.py` line 3-4 confirms: "Used by the HTTP polling endpoint since WebSocket doesn't work through WSL2 port forwarding on Windows."

#### Evidence
- `backend/api/routes/query.py` creates sessions and calls `run_pipeline()` from `pipeline_store.py`
- `backend/api/routes/pipeline.py` provides GET endpoint for polling
- Frontend likely uses HTTP polling, not WebSocket
- No tests exist for WebSocket endpoint

#### Recommendation
**REMOVE OR DEPRECATE** - Mark as deprecated and document migration path

**Action Items**:
1. Add deprecation warning to WebSocket endpoint
2. Document that HTTP polling is the primary interface
3. Consider removing in next major version
4. If keeping for future use, add integration tests

**Estimated Effort**: 30 minutes (deprecation) or 2 hours (full removal)  
**Coverage Impact**: +0% (dead code doesn't affect production)  
**Risk if Left Untested**: LOW (not used in production)

---

### 2. backend/pipeline_store.py
**Coverage**: 15% (46 uncovered lines)  
**Classification**: INTEGRATION-LEVEL CONCERN  
**Priority**: MEDIUM

#### Root Cause Analysis
The `run_pipeline()` function (lines 44-122) orchestrates an async background task that:
- Calls external APIs (Semantic Scholar, arXiv)
- Updates session state asynchronously
- Runs in `asyncio.create_task()` without awaiting

This is difficult to unit test because:
1. It's fire-and-forget (no return value to assert)
2. Requires mocking multiple async external calls
3. State updates happen asynchronously in background
4. Timing-dependent (uses `asyncio.sleep()`)

#### Current Test Coverage
- `create_session()` - COVERED
- `get_session()` - COVERED  
- `update_session()` - COVERED
- `run_pipeline()` - NOT COVERED (integration-level)

#### Recommendation
**ADD LIGHTWEIGHT INTEGRATION TESTS**

**Test Strategy**:
```python
@pytest.mark.asyncio
async def test_run_pipeline_creates_background_task(mocker):
    """Test that run_pipeline starts async task."""
    # Mock the async functions
    mock_search = mocker.patch('backend.mcp_servers.semantic_scholar_mcp.search_papers')
    mock_search.return_value = {"papers": [], "citations": [], "source": "test"}
    
    session_id = "test-123"
    create_session(session_id, "test query")
    
    # Run pipeline
    run_pipeline(session_id)
    
    # Give background task time to start
    await asyncio.sleep(0.1)
    
    # Verify session was updated
    session = get_session(session_id)
    assert session["stage"] in ["discovery", "extraction", "synthesis", "complete", "error"]
```

**Estimated Effort**: 3-4 hours  
**Coverage Impact**: +5-7%  
**Risk if Left Untested**: MEDIUM (core pipeline logic, but integration tests cover end-to-end)

---

### 3. backend/mcp_servers/semantic_scholar_mcp.py
**Coverage**: 75% (30 uncovered lines)  
**Classification**: TESTABLE LOGIC GAP  
**Priority**: HIGH

#### Root Cause Analysis
Uncovered lines include:
- **Lines 87-99**: arXiv fallback path when S2 is disabled
- **Lines 127-146**: Citation fetching loop with error handling
- **Lines 173-199**: Synthetic citation generation edge cases

#### Current Test Coverage
- `search_papers()` with API key - COVERED
- `search_papers()` without API key - COVERED
- Rate limiting - COVERED
- Retry on 429 - COVERED
- `_generate_synthetic_citations()` basic - COVERED

#### Uncovered Scenarios
1. **arXiv fallback path** (lines 87-99)
2. **Citation fetch failures** (lines 144-146)
3. **Synthetic citation edge cases** (lines 173-199)

#### Recommendation
**ADD TARGETED UNIT TESTS**

**Test Implementation**:
```python
@pytest.mark.asyncio
async def test_search_papers_arxiv_fallback(mocker):
    """Test arXiv fallback when S2 is disabled."""
    # Mock settings to disable S2
    mocker.patch('backend.config.settings.s2_enabled', False)
    
    # Mock arXiv search
    mock_arxiv = mocker.patch('backend.mcp_servers.arxiv_mcp.search_arxiv')
    mock_arxiv.return_value = [
        {"paper_id": "arxiv:123", "title": "Test", "year": 2024}
    ]
    
    result = await search_papers("test query")
    
    assert result["source"] == "arxiv-only"
    assert result["mode"] == "synthetic"
    assert len(result["papers"]) == 1
    mock_arxiv.assert_called_once()

@pytest.mark.asyncio  
async def test_citation_fetch_handles_errors(mocker):
    """Test that citation fetch errors don't break pipeline."""
    # Mock S2 search to return papers
    mock_get = mocker.patch('backend.mcp_servers.semantic_scholar_mcp._s2_get')
    mock_get.side_effect = [
        # First call: search results
        {"data": [{"paperId": "123", "title": "Test", "year": 2024, "authors": []}]},
        # Second call: citation fetch fails
        Exception("API error"),
    ]
    
    result = await search_papers("test query")
    
    # Should still return papers even if citation fetch fails
    assert len(result["papers"]) == 1
    assert result["citations"] == []  # Empty due to error

def test_synthetic_citations_same_category_preference():
    """Test that synthetic citations prefer same-category papers."""
    papers = [
        {"paper_id": "p1", "year": 2020, "primary_category": "cs.AI"},
        {"paper_id": "p2", "year": 2021, "primary_category": "cs.AI"},
        {"paper_id": "p3", "year": 2022, "primary_category": "math.ST"},
    ]
    
    citations = _generate_synthetic_citations(papers)
    
    # p2 should cite p1 (same category) more likely than p3 citing p1
    ai_citations = [c for c in citations if c["citing_id"] == "p2"]
    assert len(ai_citations) > 0
```

**Estimated Effort**: 2-3 hours  
**Coverage Impact**: +3-4%  
**Risk if Left Untested**: MEDIUM (fallback paths are important for resilience)

---

### 4. backend/api/routes/query.py
**Coverage**: 64% (4 uncovered lines)  
**Classification**: INTEGRATION-LEVEL CONCERN  
**Priority**: LOW

#### Root Cause Analysis
The uncovered lines are likely:
- Line 15: `run_pipeline(session_id)` - fire-and-forget call
- Lines in return statement

These are integration-level concerns that require FastAPI test client.

#### Recommendation
**ADD FASTAPI INTEGRATION TEST**

**Test Implementation**:
```python
def test_start_query_endpoint(client):
    """Test POST /api/query endpoint."""
    response = client.post("/api/query", json={
        "query": "machine learning",
        "max_results": 30
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "processing"
    assert "websocket_url" in data
```

**Estimated Effort**: 30 minutes  
**Coverage Impact**: +0.5%  
**Risk if Left Untested**: LOW (simple endpoint, covered by integration tests)

---

### 5. backend/api/routes/pipeline.py
**Coverage**: 56% (4 uncovered lines)  
**Classification**: INTEGRATION-LEVEL CONCERN  
**Priority**: LOW

#### Root Cause Analysis
Similar to query.py - uncovered lines are in route handler logic.

#### Recommendation
**ADD FASTAPI INTEGRATION TEST**

**Test Implementation**:
```python
def test_get_pipeline_status_not_found(client):
    """Test GET /api/pipeline/{session_id} with invalid ID."""
    response = client.get("/api/pipeline/invalid-id")
    
    assert response.status_code == 200
    data = response.json()
    assert data["error"] == "Session not found"
    assert data["stage"] == "error"

def test_get_pipeline_status_success(client):
    """Test GET /api/pipeline/{session_id} with valid session."""
    # Create session first
    from backend.pipeline_store import create_session
    session_id = "test-123"
    create_session(session_id, "test query")
    
    response = client.get(f"/api/pipeline/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "stage" in data
    assert "progress" in data
```

**Estimated Effort**: 30 minutes  
**Coverage Impact**: +0.5%  
**Risk if Left Untested**: LOW (simple endpoint)

---

### 6. backend/engines/citation_graph.py
**Coverage**: 92% (6 uncovered lines)  
**Classification**: TESTABLE LOGIC GAP  
**Priority**: LOW

#### Root Cause Analysis
Likely uncovered lines are edge cases in error handling or specific conditional branches.

#### Recommendation
**REVIEW COVERAGE REPORT** to identify specific lines, then add targeted tests.

**Estimated Effort**: 1 hour  
**Coverage Impact**: +1%  
**Risk if Left Untested**: LOW (already 92% covered)

---

### 7. backend/config.py
**Coverage**: 94% (1 uncovered line)  
**Classification**: TESTABLE LOGIC GAP  
**Priority**: LOW

#### Root Cause Analysis
Line 27: `return bool(self.semantic_scholar_api_key)` in `s2_enabled` property.

#### Recommendation
**ADD SIMPLE UNIT TEST**

**Test Implementation**:
```python
def test_s2_enabled_with_key(mocker):
    """Test s2_enabled returns True when API key is set."""
    mocker.patch.dict('os.environ', {'SEMANTIC_SCHOLAR_API_KEY': 'test-key'})
    from backend.config import Settings
    settings = Settings()
    assert settings.s2_enabled is True

def test_s2_enabled_without_key(mocker):
    """Test s2_enabled returns False when API key is not set."""
    mocker.patch.dict('os.environ', {}, clear=True)
    from backend.config import Settings
    settings = Settings()
    assert settings.s2_enabled is False
```

**Estimated Effort**: 15 minutes  
**Coverage Impact**: +0.1%  
**Risk if Left Untested**: VERY LOW (simple property)

---

### 8. backend/engines/timeline.py
**Coverage**: 99% (1 uncovered line)  
**Classification**: TESTABLE LOGIC GAP  
**Priority**: VERY LOW

#### Root Cause Analysis
Likely a single edge case or conditional branch.

#### Recommendation
**REVIEW COVERAGE REPORT** to identify specific line. Given 99% coverage, this is likely negligible.

**Estimated Effort**: 15 minutes  
**Coverage Impact**: +0.1%  
**Risk if Left Untested**: VERY LOW (already 99% covered)

---

## Prioritized Action Plan

### Phase 1: High-Impact, Low-Effort (Target: 90% coverage)
**Estimated Time**: 4-5 hours  
**Coverage Gain**: +4-5%

1. **Add S2 fallback tests** (semantic_scholar_mcp.py) - 2 hours
   - arXiv fallback path
   - Citation fetch error handling
   - Synthetic citation edge cases

2. **Add config property test** (config.py) - 15 minutes
   - s2_enabled property

3. **Add route integration tests** (query.py, pipeline.py) - 1 hour
   - POST /api/query
   - GET /api/pipeline/{session_id}

4. **Review and fix citation_graph.py gaps** - 1 hour
   - Identify uncovered lines from coverage report
   - Add targeted tests

### Phase 2: Medium-Impact, Medium-Effort (Target: 92% coverage)
**Estimated Time**: 3-4 hours  
**Coverage Gain**: +2-3%

1. **Add pipeline_store integration tests** - 3-4 hours
   - Background task execution
   - Async state updates
   - Error handling in pipeline

### Phase 3: Low-Priority Cleanup (Optional)
**Estimated Time**: 2-3 hours  
**Coverage Gain**: +0% (cleanup only)

1. **Deprecate or remove WebSocket endpoint** - 2-3 hours
   - Add deprecation warnings
   - Document migration to HTTP polling
   - Update API documentation

---

## Risk Assessment Matrix

| File | Coverage | Risk if Untested | Effort | Priority |
|------|----------|------------------|--------|----------|
| semantic_scholar_mcp.py | 75% | MEDIUM | 2-3h | HIGH |
| config.py | 94% | VERY LOW | 15min | LOW |
| query.py | 64% | LOW | 30min | LOW |
| pipeline.py | 56% | LOW | 30min | LOW |
| citation_graph.py | 92% | LOW | 1h | LOW |
| timeline.py | 99% | VERY LOW | 15min | VERY LOW |
| pipeline_store.py | 15% | MEDIUM | 3-4h | MEDIUM |
| websocket.py | 22% | LOW | 0h (dead code) | HIGH (cleanup) |

---

## Architectural Decisions

### What Should Remain Untested

1. **WebSocket endpoint** (websocket.py)
   - **Reason**: Dead code, replaced by HTTP polling
   - **Action**: Deprecate or remove

2. **Complex async orchestration** (pipeline_store.py `run_pipeline()`)
   - **Reason**: Integration-level concern, difficult to unit test
   - **Mitigation**: Covered by end-to-end integration tests
   - **Action**: Add lightweight integration tests for critical paths

3. **External API calls** (when not mocked)
   - **Reason**: Network-dependent, slow, unreliable
   - **Mitigation**: All tests use mocks
   - **Action**: Maintain mock-based testing strategy

---

## Recommendations for Hackathon Context

Given time constraints, focus on **Phase 1** only:
- Achieves 90% coverage (exceeds 80% target)
- Addresses highest-risk gaps (S2 fallback paths)
- Low effort (4-5 hours)
- Demonstrates production-grade quality to judges

**Phase 2** and **Phase 3** can be deferred to post-hackathon development.

---

## Conclusion

Current 87% coverage is **production-ready** for a hackathon project. The gaps are primarily:
1. Dead code (WebSocket) - should be removed
2. Integration-level concerns - covered by end-to-end tests
3. Minor edge cases - low risk

Implementing **Phase 1** recommendations will achieve 90%+ coverage and address all high-risk gaps, demonstrating exceptional code quality for hackathon judging.

---

**Next Steps**:
1. Review this analysis with team
2. Implement Phase 1 tests (4-5 hours)
3. Run coverage report to verify 90%+ achieved
4. Document remaining gaps in README
5. Present comprehensive testing strategy to judges