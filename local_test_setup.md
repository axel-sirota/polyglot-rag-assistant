# Local Test Setup & Deployment Guide

## Script Analysis & Cleanup Recommendations

### 🚨 Current Script Confusion
The root directory has 22 script files (.py and .sh) creating unnecessary complexity. Here's the analysis:

### ✅ ESSENTIAL SCRIPTS (Keep These)

#### Core Application Entry Points:
1. **main.py** - Main orchestrator that initializes all agents and services
2. **api_server.py** - FastAPI server for LiveKit token generation
3. **livekit_voice_assistant.py** - LiveKit agent with voice capabilities

#### Frontend Entry Points:
4. **frontend/gradio_app.py** - Main Gradio interface (accessed via scripts)
5. **frontend/realtime_gradio_app.py** - Realtime voice interface

#### Deployment Scripts:
6. **scripts/start-demo.sh** - Main demo launcher (comprehensive)
7. **scripts/start-realtime-demo.sh** - Realtime demo launcher
8. **deploy_livekit_cloud.sh** - LiveKit cloud deployment

### ❌ REDUNDANT/CONFUSING SCRIPTS (Delete These)

#### Duplicate/Test Scripts:
- **simple_voice_agent.py** - Duplicate of livekit_voice_assistant.py
- **working_voice_agent.py** - Another duplicate
- **voice_agent_fixed.py** - Yet another duplicate
- **tim_style_agent.py** - Experimental duplicate
- **minimal_agent.py** - Minimal test version
- **test_agent_connection.py** - One-off test script

#### Test Scripts (Move to tests/ or delete):
- **test_gradio.py** - Simple gradio test
- **test_gradio_simple.py** - Another gradio test
- **test_minimal.py** - Minimal test
- **quick_demo.py** - Quick demo script
- **start_app.py** - Wrapper for gradio_app.py (unnecessary)

#### Redundant Shell Scripts:
- **test_local.sh** - Redundant with start-demo.sh
- **test_clean.sh** - Just kills processes
- **simple_test.sh** - Another test script
- **quick_test.sh** - Yet another test script
- **start_livekit_demo.sh** - Old version

#### Other:
- **deploy_aws_ecs.sh** - AWS deployment (not for local/demo)
- **setup.py** - Not needed for demo

### 📁 FOLDER ANALYSIS

#### Essential Folders:
- **agents/** - Core agent implementations
- **services/** - Business logic services  
- **frontend/** - Gradio interfaces
- **scripts/** - Deployment scripts
- **utils/** - Utilities (logging)
- **.venv/** - Virtual environment
- **logs/** - Log files

#### Can Be Removed:
- **api/** - Only has empty __init__.py and unused main.py
- **mcp_servers/** - Empty folder (MCP not available)
- **web-app/** - HTML interface (not needed if using Gradio)
- **mobile-app/** - React Native (not ready for demo)
- **tests/** - Can keep but not essential for demo
- **.mypy_cache/** - Type checking cache

## 🚀 SIMPLIFIED DEPLOYMENT INSTRUCTIONS

### Prerequisites
```bash
# 1. Ensure Python 3.10+ is installed
python3 --version

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
.venv/bin/python3 -m pip install -r requirements.txt

# 4. Create .env file with your API keys:
cat > .env << EOF
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
LIVEKIT_API_KEY=your-livekit-key
LIVEKIT_API_SECRET=your-livekit-secret
LIVEKIT_URL=wss://your-app.livekit.cloud
EOF
```

### Quick Start (Gradio Interface)
```bash
# Option 1: Use the start script (recommended)
./scripts/start-demo.sh

# Option 2: Manual start
.venv/bin/python3 -m frontend.gradio_app
```

### LiveKit Agent Deployment
```bash
# Deploy to LiveKit Cloud
./deploy_livekit_cloud.sh

# Or run locally
.venv/bin/python3 livekit_voice_assistant.py dev
```

### Access Points
- **Gradio Interface**: http://localhost:7860
- **Public URL**: Check terminal for Gradio share link
- **Logs**: Check `logs/` directory

## 🧹 CLEANUP COMMANDS

### Remove Redundant Scripts
```bash
# Delete redundant Python scripts
rm simple_voice_agent.py working_voice_agent.py voice_agent_fixed.py tim_style_agent.py
rm minimal_agent.py test_agent_connection.py test_gradio.py test_gradio_simple.py
rm test_minimal.py quick_demo.py start_app.py

# Delete redundant shell scripts  
rm test_local.sh test_clean.sh simple_test.sh quick_test.sh start_livekit_demo.sh

# Delete setup.py (not needed)
rm setup.py

# Remove empty/unused folders
rm -rf api/ mcp_servers/
```

### Optional Cleanup (if not using)
```bash
# Remove web-app if only using Gradio
rm -rf web-app/

# Remove mobile-app if not ready
rm -rf mobile-app/

# Remove type checking cache
rm -rf .mypy_cache/
```

## 📋 SIMPLIFIED PROJECT STRUCTURE

After cleanup:
```
polyglot-rag-assistant/
├── agents/           # Voice, flight, and RAG agents
├── services/         # Core services
├── frontend/         # Gradio interfaces
├── scripts/          # Start scripts
├── utils/           # Logging utilities
├── logs/            # Application logs
├── .venv/           # Python virtual environment
├── main.py          # Main orchestrator
├── api_server.py    # FastAPI token server
├── livekit_voice_assistant.py  # LiveKit agent
├── requirements.txt
├── .env
└── README.md
```

## 🎯 DEMO WORKFLOW

1. **Start Everything**:
   ```bash
   ./scripts/start-demo.sh
   ```

2. **Test Voice Chat**:
   - Open http://localhost:7860
   - Click microphone
   - Say: "Find flights from New York to Paris"

3. **Monitor Logs**:
   ```bash
   tail -f logs/*.log
   ```

4. **Stop Everything**:
   - Press Ctrl+C in terminal
   - Or run: `pkill -f "python.*gradio"`

## 🔧 TROUBLESHOOTING

### Port Already in Use
```bash
# Kill processes on port 7860
lsof -ti:7860 | xargs kill -9
```

### Module Import Errors
```bash
# Reinstall dependencies
.venv/bin/python3 -m pip install -r requirements.txt --upgrade
```

### API Connection Issues
- Check .env file has correct API keys
- Verify internet connection
- Check logs/gradio_app.log for errors

## 📝 NOTES

- This is a DEMO project - prioritizes working code over perfection
- Use Gradio interface for quick demos
- LiveKit agent can be deployed to cloud for production
- All logging goes to logs/ directory
- Virtual environment commands use .venv/bin/python3