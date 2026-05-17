# SAGE Manual Testing Guide

## 1. Step-by-Step Manual Test Plan

### Setup
- **Starting Point**: Open http://localhost:3000 in your browser
- **Prerequisites**: Backend running on port 8000, valid S2 API key configured
- **Browser**: Chrome/Firefox (latest version recommended)

---

### Test Scenario A: Normal Happy Path Flow

**Steps:**
1. Load http://localhost:3000
2. **Expect**: Clean landing page with search input field and "Run analysis" button visible
3. Enter query: `CRISPR gene therapy`
4. Click "Run analysis"
5. **Expect**: Pipeline progress indicator appears showing 5 stages:
   - Stage 1: Fetching papers
   - Stage 2: Building citation graph
   - Stage 3: Analyzing timeline
   - Stage 4: Detecting paradigm shifts
   - Stage 5: Generating proposal
6. **Expect**: Each stage transitions from "pending" → "in progress" → "complete" with visual feedback (spinner, checkmark, or progress bar)
7. **Timing**: Entire pipeline should complete in 10–30 seconds
8. **Expect**: Four result tabs appear: Review, Citation Graph, Timeline, Proposal
9. Click each tab and verify:
   - **Review**: Summary text with paper count (~30 papers), citation count (~79 edges)
   - **Citation Graph**: Interactive graph with nodes and edges, zoom/pan controls
   - **Timeline**: Year-based visualization showing publication trends
   - **Proposal**: Generated research proposal text with sections (Introduction, Methods, etc.)
10. **Bug indicators**: Blank tabs, "undefined" text, console errors, frozen UI

---

### Test Scenario B: Empty Query

**Steps:**
1. Leave search field completely empty
2. Click "Run analysis"
3. **Expect**: Validation message appears: "Please enter a search query" or similar
4. **Bug indicators**: Pipeline starts anyway, app crashes, no feedback to user

---

### Test Scenario C: Nonsense Query

**Steps:**
1. Enter query: `asdfghjkl zxcvbnm qwerty`
2. Click "Run analysis"
3. **Expect**: Pipeline runs but Stage 1 completes with message like "No papers found" or "0 results"
4. **Expect**: Graceful handling—either show empty state message or disable subsequent stages
5. **Bug indicators**: App crashes, infinite loading, error modal without recovery option

---

### Test Scenario D: Very Long Query

**Steps:**
1. Enter query: `machine learning deep neural networks convolutional recurrent transformers attention mechanisms natural language processing computer vision reinforcement learning generative adversarial networks transfer learning meta-learning few-shot learning zero-shot learning multimodal learning self-supervised learning contrastive learning`
2. Click "Run analysis"
3. **Expect**: Query is either truncated with visual indicator OR sent as-is and S2 API handles it
4. **Expect**: Pipeline completes or shows clear error message if query exceeds API limits
5. **Bug indicators**: UI layout breaks, input field overflows, silent failure

---

### Test Scenario E: Network Interruption Simulation

**Steps:**
1. Open browser DevTools → Network tab
2. Set throttling to "Offline" or "Slow 3G"
3. Enter query: `quantum computing`
4. Click "Run analysis"
5. **Expect**: Stage 1 shows loading spinner, then timeout error after 30–60 seconds
6. **Expect**: Error message: "Network error. Please check your connection and try again."
7. **Expect**: Retry button or ability to re-run query
8. **Bug indicators**: Infinite spinner, no error message, app becomes unresponsive

---

### Test Scenario F: Rapid Repeated Queries

**Steps:**
1. Enter query: `AI ethics`
2. Click "Run analysis"
3. Immediately (before Stage 1 completes) enter new query: `blockchain`
4. Click "Run analysis" again
5. **Expect**: First request is cancelled OR queued, second request starts fresh
6. **Expect**: No duplicate results, no mixed data from both queries
7. **Bug indicators**: Results from both queries appear simultaneously, UI shows stale data

---

### Test Scenario G: Browser Back/Forward Navigation

**Steps:**
1. Complete a successful query: `neural networks`
2. Click browser back button
3. **Expect**: Return to initial empty state OR query remains in input field
4. Click browser forward button
5. **Expect**: Results reappear OR user is prompted to re-run query
6. **Bug indicators**: Blank page, broken layout, console errors

---

### Test Scenario H: Tab Switching During Pipeline

**Steps:**
1. Start query: `climate change modeling`
2. While Stage 2 is running, click to a different browser tab
3. Wait 10 seconds
4. Return to SAGE tab
5. **Expect**: Pipeline continues and completes normally
6. **Bug indicators**: Pipeline freezes, progress resets, results never appear

---

## 2. Quick Testing Checklist (10–15 Items)

### Functional Checks
- [ ] **F1**: Entered valid query "CRISPR gene therapy" → all 5 pipeline stages complete without errors
- [ ] **F2**: Empty query → validation message appears, pipeline does not start
- [ ] **F3**: Nonsense query "zzzzzz" → graceful "No results" message, no crash
- [ ] **F4**: All 4 result tabs (Review, Citation Graph, Timeline, Proposal) display content after successful query
- [ ] **F5**: Citation Graph tab → nodes and edges render, graph is interactive (zoom/pan works)

### Performance Checks
- [ ] **P1**: Pipeline completes in under 30 seconds for typical query
- [ ] **P2**: UI remains responsive during pipeline execution (can scroll, hover, click tabs)
- [ ] **P3**: No visible memory leaks—run 3 consecutive queries, check browser memory usage stays stable

### Error Handling & UX Checks
- [ ] **E1**: Simulated network failure → clear error message appears with retry option
- [ ] **E2**: Rapid double-click on "Run analysis" → no duplicate requests or mixed results
- [ ] **E3**: Very long query (100+ words) → input field handles gracefully, no layout break
- [ ] **E4**: Browser back button → app returns to initial state without breaking
- [ ] **E5**: Console shows no critical errors (red messages) during normal operation

### Visual/Layout Checks
- [ ] **V1**: All text is readable (no overlapping, no cut-off labels)
- [ ] **V2**: Loading spinners/progress indicators are visible and animate smoothly

---

## 3. High-Risk Edge Cases to Test Manually

### Edge Case 1: Papers with Missing Citation Data
**Trigger**: Query for very recent papers (2024–2025) or obscure topics where S2 data is sparse  
**Example Query**: `emerging quantum dot solar cells 2025`  
**Ideal Behavior**:
- Stage 2 (Build Citation Graph) completes but shows message: "Limited citation data available"
- Citation Graph tab displays nodes with 0 or few edges
- Timeline tab shows gaps or sparse data points
- No crashes, no "undefined" errors in UI

---

### Edge Case 2: Years Outside Valid Range (1900–2100)
**Trigger**: Manually inspect Timeline tab data—if any paper has `year: null`, `year: 1800`, or `year: 3000`  
**Simulation**: If you have backend access, temporarily modify a paper's year in the response  
**Ideal Behavior**:
- Timeline filters out invalid years silently OR displays them in a separate "Unknown" category
- No axis rendering errors (e.g., timeline stretching to year 3000)
- Proposal generation ignores or handles invalid years gracefully

---

### Edge Case 3: Semantic Scholar API Rate Limit Hit
**Trigger**: Run 10+ queries rapidly in succession (within 1 minute)  
**Ideal Behavior**:
- After ~5–10 requests, Stage 1 shows error: "API rate limit reached. Please wait 60 seconds."
- Countdown timer appears OR retry button is disabled temporarily
- No silent failures—user is clearly informed
- Subsequent queries after cooldown period work normally

---

### Edge Case 4: API Timeout (Slow S2 Response)
**Trigger**: Use browser DevTools → Network tab → set throttling to "Slow 3G"  
**Ideal Behavior**:
- Stage 1 shows loading for up to 60 seconds
- If timeout occurs, error message: "Request timed out. Please try again."
- Pipeline stops gracefully, does not proceed to Stage 2 with incomplete data
- Retry button allows user to re-attempt

---

### Edge Case 5: Malformed API Response (Missing Required Fields)
**Trigger**: Difficult to simulate without backend modification—look for queries that return papers with missing `title`, `authors`, or `paperId`  
**Example Query**: Try very niche or non-English topics  
**Ideal Behavior**:
- Backend validates response and filters out malformed papers
- Frontend displays only valid papers (e.g., "28 of 30 papers processed")
- No "undefined" or "null" text in Review or Proposal tabs
- Console logs warning but does not crash

---

### Edge Case 6: Zero Citations Found (Isolated Papers)
**Trigger**: Query for brand-new preprints or highly specialized topics  
**Example Query**: `novel protein folding algorithm 2025`  
**Ideal Behavior**:
- Stage 2 completes with message: "No citation relationships found"
- Citation Graph tab shows isolated nodes (no edges)
- Timeline tab still displays publication years
- Proposal generation adapts: "Limited citation data suggests emerging field"

---

### Edge Case 7: Browser Window Resize During Graph Rendering
**Trigger**:
1. Start query: `deep learning`
2. While Citation Graph is rendering, rapidly resize browser window (drag corner)
3. Switch to fullscreen and back

**Ideal Behavior**:
- Graph re-renders and scales to fit new window size
- No layout breaks, no overlapping elements
- Zoom/pan controls remain functional

---

## 4. Bug Report Template

```markdown
### Bug Report

**Title**: [One-line summary, e.g., "Citation Graph fails to render with >100 nodes"]

**Steps to Reproduce**:
1. Open http://localhost:3000
2. Enter query: [exact query text]
3. Click "Run analysis"
4. [Additional steps...]

**Expected Behavior**:
[What should happen according to the design/spec]

**Actual Behavior**:
[What actually happened—be specific]

**Screenshot**:
[Attach screenshot or paste image URL]

**Console Log Snippet**:
```
[Paste relevant errors from browser console—right-click → Inspect → Console tab]
```

**Environment**:
- Browser: [Chrome 120 / Firefox 115 / Safari 17]
- OS: [Windows 11 / macOS 14 / Ubuntu 22.04]
- SAGE Version: [commit hash or "latest main"]
- Timestamp: [YYYY-MM-DD HH:MM]

**Severity**:
- [ ] Critical (app crashes, data loss)
- [ ] High (major feature broken)
- [ ] Medium (workaround exists)
- [ ] Low (cosmetic issue)

**Additional Notes**:
[Any other context, e.g., "Only happens on mobile", "Intermittent—occurs 1 in 5 times"]
```

---

## Testing Tips

1. **Keep DevTools Open**: Monitor Console and Network tabs throughout testing
2. **Test in Incognito**: Avoid cached data interfering with results
3. **Take Notes**: Jot down anything that feels "off" even if it doesn't break
4. **Time Everything**: Note if any stage takes >10 seconds—potential performance issue
5. **Check Mobile**: If time permits, test on phone/tablet or use DevTools device emulation

---

## Integration with Automated Tests

This manual testing guide complements the automated test suite:
- **Automated tests** (backend/tests/) cover unit and integration testing with mocks
- **Manual tests** (this guide) cover end-to-end user flows and visual/UX validation
- **Together** they provide comprehensive coverage for production readiness

### When to Use Manual vs. Automated Testing

**Use Automated Tests For**:
- Unit testing individual functions (citation graph, timeline, MCP servers)
- Regression testing after code changes
- CI/CD pipeline validation
- Performance benchmarking

**Use Manual Tests For**:
- End-to-end user experience validation
- Visual/layout verification
- Browser compatibility testing
- Edge cases difficult to automate (network interruptions, rapid user actions)
- Accessibility testing

---

**Ready to Test?** Start with the Quick Checklist, then dive into Edge Cases. Use the Bug Report Template for anything you find. Good luck! 🚀