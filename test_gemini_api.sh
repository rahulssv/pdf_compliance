#!/bin/bash

# Test Gemini API Key
# This script tests if the Gemini API key is valid and working

echo "🔍 Testing Gemini API Key..."
echo "================================"

# Get the API key from environment or .env file
if [ -f .env ]; then
    source .env
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GEMINI_API_KEY not found in environment"
    exit 1
fi

echo "📋 API Key: ${GEMINI_API_KEY:0:10}..."
echo ""

# Test with a simple curl request to Gemini API
echo "🤖 Sending test request to Gemini API..."
echo ""

RESPONSE=$(curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key=${GEMINI_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{
      "parts": [{
        "text": "Say hello in one word"
      }]
    }]
  }')

echo "📥 Response:"
echo "$RESPONSE" | jq '.'
echo ""

# Check if response contains error
if echo "$RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
    ERROR_MESSAGE=$(echo "$RESPONSE" | jq -r '.error.message')
    ERROR_CODE=$(echo "$RESPONSE" | jq -r '.error.code')
    echo "❌ API Error (Code: $ERROR_CODE)"
    echo "   Message: $ERROR_MESSAGE"
    exit 1
fi

# Check if response contains valid content
if echo "$RESPONSE" | jq -e '.candidates[0].content.parts[0].text' > /dev/null 2>&1; then
    GENERATED_TEXT=$(echo "$RESPONSE" | jq -r '.candidates[0].content.parts[0].text')
    echo "✅ API Key is VALID!"
    echo "   Generated text: $GENERATED_TEXT"
    exit 0
else
    echo "⚠️ Unexpected response format"
    exit 1
fi

# Made with Bob
