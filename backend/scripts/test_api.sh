#!/usr/bin/env bash
set -euo pipefail

echo "Testing Meower API..."

# Health check
echo -n "Health: "
curl -s http://localhost:8000/health | python3 -m json.tool

# List tools
echo -n "Tools: "
curl -s http://localhost:8000/api/v1/tools | python3 -m json.tool

# Create investigation
echo -n "Create investigation: "
curl -s -X POST http://localhost:8000/api/v1/investigations \
  -H "Content-Type: application/json" \
  -d '{"seed": "john@example.com", "type": "email"}' | python3 -m json.tool

echo "Done!"
