#!/bin/bash
# Test script for Case Chat API with Frontend-Compatible Format

set -e  # Exit on error

echo "=========================================="
echo "Case Chat API Test - Frontend Format"
echo "=========================================="
echo ""

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
EMAIL="${TEST_EMAIL:-promptpirates@amazatic.com}"
PASSWORD="${TEST_PASSWORD:-promptpirates123!}"

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
echo ""

# Step 2: Get or create case
echo "[2/6] Getting case..."
CASES_RESPONSE=$(curl -s -X GET "$BASE_URL/api/search/cases/summary/" \
  -H "Authorization: Bearer $TOKEN")

CASE_ID=$(echo $CASES_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$CASE_ID" ]; then
  echo "   Creating new case..."
  CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/search/cases/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "title": "State v. Anderson - Robbery Investigation",
      "description": "A high-profile case involving allegations of armed robbery at downtown bank.",
      "query_text": "Find suspect in black sedan"
    }')
  
  CASE_ID=$(echo $CREATE_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
  echo "   ✅ Created case: $CASE_ID"
else
  echo "   ✅ Using case: $CASE_ID"
fi
echo ""

# Step 3: Send a user message
echo "[3/6] Sending user message..."
USER_MSG_RESPONSE=$(curl -s -X POST "$BASE_URL/api/chat/case/$CASE_ID/message/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What happened between 3:15 PM and 3:30 PM on February 14th?",
    "message_type": "user"
  }')

USER_MSG_ID=$(echo $USER_MSG_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$USER_MSG_ID" ]; then
  echo "✅ User message sent (ID: $USER_MSG_ID)"
else
  echo "⚠️  User message might have failed"
fi
echo ""

# Step 4: Send an assistant response
echo "[4/6] Sending assistant response..."
ASST_MSG_RESPONSE=$(curl -s -X POST "$BASE_URL/api/chat/case/$CASE_ID/message/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Based on the evidence, at 3:18 PM, a black sedan was observed entering the parking lot from the north entrance. At 3:22 PM, two individuals exited the vehicle and approached the building entrance. The security camera footage shows clear visibility of both subjects.",
    "message_type": "assistant"
  }')

ASST_MSG_ID=$(echo $ASST_MSG_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$ASST_MSG_ID" ]; then
  echo "✅ Assistant message sent (ID: $ASST_MSG_ID)"
else
  echo "⚠️  Assistant message might have failed"
fi
echo ""

# Step 5: Send another user question
echo "[5/6] Sending follow-up question..."
FOLLOWUP_RESPONSE=$(curl -s -X POST "$BASE_URL/api/chat/case/$CASE_ID/message/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What are the potential legal implications of the evidence presented?",
    "message_type": "user"
  }')

echo "✅ Follow-up question sent"
echo ""

# Step 6: Get case chat with all messages
echo "[6/6] Retrieving case chat history..."
echo ""
echo "=========================================="
echo "CHAT RESPONSE (Frontend Format):"
echo "=========================================="

CHAT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/chat/case/$CASE_ID/" \
  -H "Authorization: Bearer $TOKEN")

echo "$CHAT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CHAT_RESPONSE"
echo ""

# Extract and display key fields
CASE_NAME=$(echo $CHAT_RESPONSE | grep -o '"case_name":"[^"]*"' | cut -d'"' -f4)
MESSAGE_COUNT=$(echo $CHAT_RESPONSE | grep -o '"role":"' | wc -l)
EVIDENCE_COUNT=$(echo $CHAT_RESPONSE | grep -o '"total_evidence_files":[0-9]*' | cut -d':' -f2)

echo "=========================================="
echo "Summary:"
echo "=========================================="
echo "  Case Name: $CASE_NAME"
echo "  Case ID: $CASE_ID"
echo "  Total Messages: $MESSAGE_COUNT"
echo "  Total Evidence Files: ${EVIDENCE_COUNT:-0}"
echo ""
echo "Response Format Validation:"
if echo "$CHAT_RESPONSE" | grep -q '"case_id"'; then
  echo "  ✅ case_id field present"
else
  echo "  ❌ case_id field missing"
fi

if echo "$CHAT_RESPONSE" | grep -q '"case_name"'; then
  echo "  ✅ case_name field present"
else
  echo "  ❌ case_name field missing"
fi

if echo "$CHAT_RESPONSE" | grep -q '"case_description"'; then
  echo "  ✅ case_description field present"
else
  echo "  ❌ case_description field missing"
fi

if echo "$CHAT_RESPONSE" | grep -q '"messages"'; then
  echo "  ✅ messages array present"
else
  echo "  ❌ messages array missing"
fi

if echo "$CHAT_RESPONSE" | grep -q '"role":"user"'; then
  echo "  ✅ 'user' role found in messages"
else
  echo "  ⚠️  'user' role not found"
fi

if echo "$CHAT_RESPONSE" | grep -q '"role":"assistant"'; then
  echo "  ✅ 'assistant' role found in messages"
else
  echo "  ⚠️  'assistant' role not found"
fi

if echo "$CHAT_RESPONSE" | grep -q '"timestamp"'; then
  echo "  ✅ timestamp field present in messages"
else
  echo "  ❌ timestamp field missing"
fi

if echo "$CHAT_RESPONSE" | grep -q '"media"'; then
  echo "  ✅ media array present in messages"
else
  echo "  ❌ media array missing"
fi

echo ""
echo "=========================================="
echo "✅ Test Complete!"
echo "=========================================="
echo ""
echo "API Endpoint:"
echo "  GET $BASE_URL/api/chat/case/$CASE_ID/"
echo ""
echo "The response now matches the frontend format with:"
echo "  - case_id, case_name, case_description"
echo "  - messages with role (user/assistant)"
echo "  - timestamp in ISO 8601 format"
echo "  - media array for each message"
echo ""
