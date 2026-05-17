# SAGE MCP Server Setup Guide for Bob
# =====================================
#
# Bob connects to MCP servers via SSH to your WSL2 machine.
# SSH address: jae@172.22.119.97 (port 22)
# Workspace:   /home/jae/sage
#
# OPTION A: Bob MCP Config File (paste into Bob's MCP settings)
# --------------------------------------------------------------
# If Bob uses a JSON config file, paste the contents of:
#   /home/jae/sage/mcp_servers/bob-mcp-config.json
#
# Then replace:
#   YOUR_DEEPL_API_KEY_HERE         → your actual DeepL API key
#   YOUR_SEMANTIC_SCHOLAR_KEY_HERE  → your actual S2 API key (optional but recommended)
#
# OPTION B: Bob UI (manual entry)
# --------------------------------
# Add two MCP servers in Bob's settings:
#
# Server 1: deepl
#   Command: npx
#   Args:    ["deepl-mcp-server"]
#   Env:     DEEPL_API_KEY=your-key-here
#
# Server 2: paper_search
#   Command: uv
#   Args:    ["run", "--with", "paper-search-mcp", "python", "/home/jae/sage/mcp_servers/paper_search/run.py"]
#   Env:     SEMANTIC_SCHOLAR_API_KEY=your-key-here
#
# Verifying from Bob
# ------------------
# Once connected, ask Bob:
#   "List your MCP tools"
# You should see:
#   - deepl: translate_text, rephrase_text, etc.
#   - paper_search: search_papers, download_paper, etc.
#
# Test with:
#   "Use paper_search to search for CRISPR gene therapy clinical trials 2020-2025"
#   "Use deepl to translate 'Hello world' to Spanish"
#
# Prerequisites on WSL2 (already installed)
# ------------------------------------------
# Node.js v20.20.2  ✓
# npm 11.14.1        ✓
# uv 0.11.13         ✓
# deepl-mcp-server   ✓ (installed globally at /home/jae/.local/bin/)
# paper-search-mcp   ✓ (available via uvx/uv run)
#
# SSH Setup (if Bob asks for SSH)
# -------------------------------
# 1. Ensure SSH server is running in WSL2:
#    sudo service ssh start
#
# 2. If SSH not installed:
#    sudo apt install openssh-server
#    sudo service ssh start
#
# 3. Bob connects to:
#    Host: 172.22.119.97
#    Port: 22
#    User: jae
#    Workspace: /home/jae/sage