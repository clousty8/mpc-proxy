#!/bin/bash

# Script de test des endpoints MCP
# Usage: ./test_mcp.sh [BASE_URL]

BASE_URL=${1:-"http://localhost:5002"}

echo "🧪 Test MCP Proxy SanteCall"
echo "📍 URL: $BASE_URL"
echo "================================"
echo ""

# Test 1: Health check
echo "1️⃣  Health Check (GET /)"
echo "---"
curl -s "$BASE_URL/" | python3 -m json.tool
echo ""
echo ""

# Test 2: tools/list
echo "2️⃣  Tools List (POST /mcp - tools/list)"
echo "---"
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }' | python3 -m json.tool
echo ""
echo ""

# Test 3: tools/call - search_patient
echo "3️⃣  Search Patient (POST /mcp - tools/call)"
echo "---"
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "search_patient",
      "arguments": {
        "phone": "+33678951483"
      }
    }
  }' | python3 -m json.tool
echo ""
echo ""

# Test 4: Erreur - outil inconnu
echo "4️⃣  Error Test - Unknown Tool"
echo "---"
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "unknown_tool",
      "arguments": {}
    }
  }' | python3 -m json.tool
echo ""
echo ""

# Test 5: Erreur - méthode inconnue
echo "5️⃣  Error Test - Unknown Method"
echo "---"
curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "unknown/method",
    "params": {}
  }' | python3 -m json.tool
echo ""
echo ""

echo "================================"
echo "✅ Tests terminés"
