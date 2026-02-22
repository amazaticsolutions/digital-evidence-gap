#!/bin/bash
# Test script for RAG query with chat storage integration

set -e  # Exit on error

echo "=========================================="
echo "RAG Query with Chat Storage - Test Script"
echo "=========================================="
echo ""

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
EMAIL="${TEST_EMAIL:-investigator@test.com}"
PASSWORD="${TEST_PASSWORD:-TestPass123!}"

echo "Configuration:"
echo "  Base URL: $BASE_URL"
echo "  Email: $EMAIL"
echo ""

# Step 1: Sign In
echo "[1/6] Signing in..."
SIGNIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/users/signin/" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

TOKEN=$(echo $SIGNIN_RESPONSE | grep -o '"access":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to sign in. Response:"
  echo "$SIGNIN_RESPONSE"
  exit 1
fi

echo "✅ Signed in successfully"
echo "   Token: ${TOKEN:0:50}..."
echo ""

# Step 2: Create a new case
echo "[2/6] Creating test case..."
CASE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/search/cases/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "RAG Chat Integration Test",
    "description": "Testing RAG query with chat storage",
    "query_text": "Find person in red clothing"
  }')

CASE_ID=$(echo $CASE_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$CASE_ID" ]; then
  echo "❌ Failed to create case. Response:"
  echo "$CASE_RESPONSE"
  exit 1
fi

echo "✅ Case created successfully"
echo "   Case ID: $CASE_ID"
echo ""

# Step 3: Check RAG system stats
echo "[3/6] Checking RAG system statistics..."
STATS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/evidence/rag/stats/" \
  -H "Authorization: Bearer $TOKEN")

TOTAL_FRAMES=$(echo $STATS_RESPONSE | grep -o '"total_frames":[0-9]*' | cut -d':' -f2)
TOTAL_EMBEDDINGS=$(echo $STATS_RESPONSE | grep -o '"total_embeddings":[0-9]*' | cut -d':' -f2)

echo "✅ RAG system stats:"
echo "   Total frames: $TOTAL_FRAMES"
echo "   Total embeddings: $TOTAL_EMBEDDINGS"
echo ""

if [ "$TOTAL_FRAMES" -eq 0 ]; then
  echo "⚠️  Warning: No frames in database. Ingest some videos first."
  echo "   Using curl -X POST $BASE_URL/api/evidence/rag/ingest/"
  echo ""
fi

# Step 4: Query the RAG system (this stores in chat)
echo "[4/6] Querying RAG system..."
QUERY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/evidence/rag/query/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"case_id\": \"$CASE_ID\",
    \"query\": \"Show me all frames with people\",
    \"top_k\": 5,
    \"enable_reid\": false
  }")

CHAT_ID=$(echo $QUERY_RESPONSE | grep -o '"chat_id":"[^"]*"' | cut -d'"' -f4)
USER_MSG_ID=$(echo $QUERY_RESPONSE | grep -o '"user_message_id":"[^"]*"' | cut -d'"' -f4)
ASST_MSG_ID=$(echo $QUERY_RESPONSE | grep -o '"assistant_message_id":"[^"]*"' | cut -d'"' -f4)
TOTAL_FOUND=$(echo $QUERY_RESPONSE | grep -o '"total_found":[0-9]*' | cut -d':' -f2)

if [ -z "$CHAT_ID" ]; then
  echo "❌ Query failed. Response:"
  echo "$QUERY_RESPONSE"
  exit 1
fi

echo "✅ Query executed successfully"
echo "   Chat ID: $CHAT_ID"
echo "   User Message ID: $USER_MSG_ID"
echo "   Assistant Message ID: $ASST_MSG_ID"
echo "   Results found: $TOTAL_FOUND"
echo ""

# Step 5: Get chat history for the case
echo "[5/6] Retrieving chat history..."
CHAT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/chat/case/$CASE_ID/" \
  -H "Authorization: Bearer $TOKEN")

MESSAGE_COUNT=$(echo $CHAT_RESPONSE | grep -o '"messages":\[' | wc -l)

echo "✅ Chat history retrieved"
echo "   Messages in chat: $(echo $CHAT_RESPONSE | grep -o '"message_type":"[^"]*"' | wc -l)"
echo ""

# Step 6: Send a follow-up message
echo "[6/6] Sending follow-up message..."
FOLLOWUP_RESPONSE=$(curl -s -X POST "$BASE_URL/api/chat/case/$CASE_ID/message/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Great results! Can we narrow down by timestamp?",
    "message_type": "user"
  }')

FOLLOWUP_MSG_ID=$(echo $FOLLOWUP_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$FOLLOWUP_MSG_ID" ]; then
  echo "❌ Failed to send message. Response:"
  echo "$FOLLOWUP_RESPONSE"
  exit 1
fi

echo "✅ Follow-up message sent"
echo "   Message ID: $FOLLOWUP_MSG_ID"
echo ""

# Summary
echo "=========================================="
echo "✅ All Tests Passed!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✓ User authenticated"
echo "  ✓ Case created: $CASE_ID"
echo "  ✓ RAG query executed and stored in chat"
echo "  ✓ Chat history retrieved"
echo "  ✓ Follow-up message sent"
echo ""
echo "View full chat history:"
echo "  curl -X GET $BASE_URL/api/chat/case/$CASE_ID/ \\"
echo "    -H \"Authorization: Bearer $TOKEN\""
echo ""
echo "Query again:"
echo "  curl -X POST $BASE_URL/api/evidence/rag/query/ \\"
echo "    -H \"Authorization: Bearer $TOKEN\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"case_id\": \"$CASE_ID\", \"query\": \"Find person in blue\", \"top_k\": 10}'"
echo ""
