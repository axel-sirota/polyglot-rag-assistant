#!/bin/bash

# Script to check the status of the Polyglot Flight Agent

echo "📊 Agent Status Check"
echo "===================="
echo ""

# Check if container is running
if docker ps | grep -q polyglot-agent; then
    echo "✅ Container is running"
    echo ""
    
    # Show container details
    echo "Container details:"
    docker ps --filter name=polyglot-agent --format "table {{.ID}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    # Show recent logs summary
    echo "Recent activity (last 10 lines):"
    docker logs --tail 10 polyglot-agent
    echo ""
    
    # Count processes
    PROCESSES=$(docker logs polyglot-agent 2>&1 | grep "process initialized" | wc -l)
    echo "🔢 Worker processes initialized: $PROCESSES"
    
    # Check for errors
    ERRORS=$(docker logs polyglot-agent 2>&1 | grep -i "error" | wc -l)
    if [ $ERRORS -gt 0 ]; then
        echo "⚠️  Found $ERRORS error messages in logs"
    else
        echo "✅ No errors found in logs"
    fi
else
    echo "❌ Container is not running"
    echo ""
    
    # Check if container exists but stopped
    if docker ps -a | grep -q polyglot-agent; then
        echo "Container exists but is stopped. Status:"
        docker ps -a --filter name=polyglot-agent --format "table {{.ID}}\t{{.Status}}"
        echo ""
        echo "Last logs before stop:"
        docker logs --tail 20 polyglot-agent
    else
        echo "No container found. Run ./run-docker.sh to start."
    fi
fi