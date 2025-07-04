#!/bin/bash
# Run all tests for Polyglot RAG Assistant

echo "🚀 Running Polyglot RAG Assistant Tests"
echo "======================================"

# Activate virtual environment if needed
if [ -d ".venv" ]; then
    source .venv/bin/activate 2>/dev/null || true
fi

# Run the test suite
.venv/bin/python3 tests/run_all_tests.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Tests completed successfully!"
else
    echo ""
    echo "⚠️  Some tests failed. Check the output above."
fi