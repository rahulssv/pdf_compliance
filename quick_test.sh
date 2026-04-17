#!/bin/bash

echo "🧪 Quick API Test - PDF Compliance Engine"
echo "========================================"
echo ""

BASE_URL="http://localhost:8000"

echo "1️⃣ Health Check"
echo "----------------"
curl -s ${BASE_URL}/health | python3 -m json.tool
echo ""
echo ""

echo "2️⃣ Scan Endpoint (Single File)"
echo "-------------------------------"
curl -s -X POST ${BASE_URL}/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/accessible_guide.pdf"]}' \
  | python3 -m json.tool
echo ""
echo ""

curl -s -X POST ${BASE_URL}/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/missing_alttext.pdf"]}' \
  | python3 -m json.tool
echo ""
echo ""

curl -s -X POST ${BASE_URL}/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/partial_form.pdf"]}' \
  | python3 -m json.tool
echo ""
echo ""
curl -s -X POST ${BASE_URL}/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/scanned_policy5.pdf"]}' \
  | python3 -m json.tool
echo ""
echo ""
curl -s -X POST ${BASE_URL}/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/untagged_report3.pdf"]}' \
  | python3 -m json.tool
echo ""
echo ""

echo "3️⃣ Remediate Endpoint (Gemini AI)"
echo "----------------------------------"
curl -s -X POST ${BASE_URL}/api/v1/remediate \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/scanned_policy5.pdf"]}' \
  | python3 -m json.tool | head -40
echo "..."
echo ""
echo ""

echo "4️⃣ Dashboard Endpoint (2 Files)"
echo "--------------------------------"
curl -s -X POST ${BASE_URL}/api/v1/dashboard \
  -H "Content-Type: application/json" \
  -d '{"fileUrls": ["/evaluator/assets/untagged_report.pdf", "/evaluator/assets/accessible_guide.pdf"]}' \
  | python3 -m json.tool
echo ""

echo "✅ All tests complete!"
