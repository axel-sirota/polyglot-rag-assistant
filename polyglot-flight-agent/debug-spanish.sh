#!/bin/bash

# Script to debug Spanish language issues in the agent

echo "🔍 Debugging Spanish language support..."
echo "Filtering for language-related logs..."
echo ""

docker logs -f polyglot-agent 2>&1 | grep -E --color=always "language|Language|metadata|Spanish|🇪🇸|es|Deepgram|participant|Final language selection"