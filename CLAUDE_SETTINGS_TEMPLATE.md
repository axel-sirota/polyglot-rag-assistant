# Claude Settings Configuration

To auto-approve common commands for this project, add the following to your Claude settings files:

## For Global Settings: `~/.claude/settings.json`

```json
{
  "auto_approve_patterns": {
    "bash": [
      "pkill -f \"python.*\" || true",
      ".venv/bin/python3 * > *.log 2>&1 &",
      "cd * && python3 -m http.server * > *.log 2>&1 &",
      "sleep * && curl *",
      "lsof -i :* | grep LISTEN*",
      "kill *",
      "tail *",
      "ls *",
      "mkdir -p *",
      "curl *",
      "cat *.log | grep *",
      "find . -name \"*.log\"*",
      "ps aux | grep python"
    ]
  }
}
```

## For Project-Specific Settings: `~/.claude/settings.local.json` 

Or create in your project root as `.claude/settings.json`:

```json
{
  "auto_approve_patterns": {
    "bash": [
      "pkill -f \"python.*api_server.py\" || true",
      "pkill -f \"python.*http.server\" || true",
      "pkill -f \"python.*api_server.py\" || true && pkill -f \"python.*http.server\" || true",
      ".venv/bin/python3 api_server.py > api_server.log 2>&1 &",
      "cd web-app && python3 -m http.server 3000 > ../web_server.log 2>&1 &",
      "sleep * && curl -s http://localhost:8000/health | jq . && echo \"✅ API server is running\" && curl -s -I http://localhost:3000 | head -1 && echo \"✅ Web server is running\"",
      "lsof -i :8000 | grep LISTEN",
      "lsof -i :3000 | grep LISTEN",
      "tail -* api_server.log*",
      "tail -f logs/*",
      "curl -s http://localhost:8000/*",
      "curl -X POST http://localhost:8000/*",
      ".venv/bin/python3 test_*.py"
    ]
  },
  "auto_approve_commands": [
    "sleep",
    "curl", 
    "pkill",
    "kill",
    "lsof",
    "tail",
    "ls",
    "mkdir",
    "cat",
    "grep",
    "find",
    "ps",
    "echo",
    "cd",
    "jq",
    "head",
    "awk",
    "xargs"
  ]
}
```

## How to Apply

1. Create the directory if it doesn't exist:
   ```bash
   mkdir -p ~/.claude
   ```

2. Create or edit `~/.claude/settings.json` with the global settings above

3. For project-specific settings, you can either:
   - Add to `~/.claude/settings.local.json` 
   - Or create `.claude/settings.json` in your project root

These settings will auto-approve the common development commands without asking for permission each time.