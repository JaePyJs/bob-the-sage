# SAGE — Bob MCP Setup & SSH Connection Guide

## SSH Connection (for Bob IDE)

| Field | Value |
|-------|-------|
| Host | `172.22.119.97` |
| Port | `22` |
| Username | `jae` |
| Password | `sage2026` |
| Workspace | `/home/jae/sage` |

SSH server is running and verified. Key-based auth also available:
- Public key: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN9rodv40HZhHykeTlODKgVXoizwNzgqCxe7SG3pvSBC sage-bob`

---

## MCP Servers Installed

### 1. DeepL MCP (translation)
- **Location:** `/home/jae/.local/bin/deepl-mcp-server`
- **Transport:** stdio
- **Env required:** `DEEPL_API_KEY`
- **Tools:** `translate_text`, `rephrase_text`, etc.

### 2. Paper Search MCP (academic papers)
- **Location:** `/home/jae/sage/mcp_servers/paper_search/run.py`
- **Runner:** `uv run --with paper-search-mcp python ...`
- **Transport:** stdio
- **Sources:** arXiv, PubMed, bioRxiv, medRxiv, Google Scholar, Semantic Scholar, Crossref, OpenAlex, and 15+ more
- **Tools:** `search_arxiv`, `search_pubmed`, `search_google_scholar`, `download_arxiv`, etc.
- **Env optional:** `SEMANTIC_SCHOLAR_API_KEY` (improves rate limits)

---

## Bob MCP Config (paste into Bob's MCP settings)

```json
{
  "mcpServers": {
    "deepl": {
      "command": "npx",
      "args": ["deepl-mcp-server"],
      "env": {
        "DEEPL_API_KEY": "YOUR_DEEPL_KEY"
      }
    },
    "paper_search": {
      "command": "uv",
      "args": ["run", "--with", "paper-search-mcp", "python", "/home/jae/sage/mcp_servers/paper_search/run.py"],
      "env": {
        "SEMANTIC_SCHOLAR_API_KEY": "YOUR_S2_KEY"
      }
    }
  }
}
```

Replace `YOUR_DEEPL_KEY` and `YOUR_S2_KEY` with actual keys.

---

## Verification Commands

After connecting Bob to SSH + MCP, test with:

```
"List your MCP tools"
"Use paper_search to search for CRISPR gene therapy clinical trials 2020-2025"
"Use deepl to translate 'Hello world' to Spanish"
```

---

## Prerequisites (all installed)

| Component | Version | Status |
|-----------|---------|--------|
| Node.js | v20.20.2 | ✓ |
| npm | 11.14.1 | ✓ |
| uv | 0.11.13 | ✓ |
| openssh-server | running | ✓ |
| deepl-mcp-server | global | ✓ |
| paper-search-mcp | via uv | ✓ |