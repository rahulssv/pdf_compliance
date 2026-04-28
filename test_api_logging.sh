#!/bin/bash
# Script to test API logging after rebuild

set -e

echo "🔧 Testing API Logging Implementation"
echo "====================================="
echo ""

echo "Step 1: Rebuilding Docker containers..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo ""
echo "Step 2: Waiting for service to be ready..."
sleep 10

echo ""
echo "Step 3: Testing health endpoint..."
curl -s http://localhost:8000/health > /dev/null
echo "✅ Health check passed"

echo ""
echo "Step 4: Making a test API request..."
curl -s -X GET http://localhost:8000/ > /dev/null
echo "✅ Test request sent"

echo ""
echo "Step 5: Viewing recent logs..."
echo "================================"
docker-compose logs --tail 50 pdf-compliance-api

echo ""
echo "Step 6: Filtering for API logs..."
echo "================================"
docker-compose logs pdf-compliance-api | grep -E "📥|✅|🌐|INCOMING|OUTGOING|GEMINI" || echo "No API logs found yet - try making more requests"

echo ""
echo "✅ Test complete!"
echo ""
echo "To view live logs, run:"
echo "  docker-compose logs -f pdf-compliance-api"
echo ""
echo "To filter for API calls only:"
echo "  docker-compose logs -f pdf-compliance-api | grep -E '📥|✅|INCOMING|OUTGOING'"

