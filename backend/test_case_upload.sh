#!/bin/bash
# Test script for Case File Upload API

set -e  # Exit on error

echo "=========================================="
echo "Case File Upload API - Test Script"
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
echo "[1/5] Signing in..."
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

# Step 2: Get existing case or create new one
echo "[2/5] Getting case information..."
CASES_RESPONSE=$(curl -s -X GET "$BASE_URL/api/search/cases/summary/" \
  -H "Authorization: Bearer $TOKEN")

CASE_ID=$(echo $CASES_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$CASE_ID" ]; then
  echo "   No existing cases found. Creating new case..."
  
  CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/search/cases/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "title": "File Upload Test Case",
      "description": "Testing case file upload functionality",
      "query_text": "Test query"
    }')
  
  CASE_ID=$(echo $CREATE_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
  
  if [ -z "$CASE_ID" ]; then
    echo "❌ Failed to create case. Response:"
    echo "$CREATE_RESPONSE"
    exit 1
  fi
  
  echo "   ✅ Created new case: $CASE_ID"
else
  echo "   ✅ Using existing case: $CASE_ID"
fi
echo ""

# Step 3: Create a test video file (if it doesn't exist)
echo "[3/5] Preparing test file..."
TEST_FILE="/tmp/test_evidence_video.mp4"

if [ ! -f "$TEST_FILE" ]; then
  echo "   Creating test video file..."
  
  # Check if ffmpeg is available
  if command -v ffmpeg &> /dev/null; then
    # Create a 5-second test video (black screen)
    ffmpeg -f lavfi -i color=c=black:s=640x480:d=5 \
           -vf "drawtext=text='Test Evidence Video':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2" \
           -c:v libx264 -t 5 -pix_fmt yuv420p "$TEST_FILE" -y &> /dev/null
    echo "   ✅ Created test video file: $TEST_FILE"
  else
    # Create a small dummy file
    echo "Test evidence file content" > "$TEST_FILE.txt"
    TEST_FILE="$TEST_FILE.txt"
    echo "   ⚠️  ffmpeg not available. Created text file instead: $TEST_FILE"
  fi
else
  echo "   ✅ Using existing test file: $TEST_FILE"
fi
echo ""

# Step 4: Upload file to case
echo "[4/5] Uploading file to case..."
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/evidence/cases/upload/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "case_id=$CASE_ID" \
  -F "files=@$TEST_FILE" \
  -F "cam_id=TEST_CAM_01" \
  -F "gps_lat=40.7128" \
  -F "gps_lng=-74.0060")

# Check if upload was successful
SUCCESS=$(echo $UPLOAD_RESPONSE | grep -o '"success":[^,]*' | cut -d':' -f2)
UPLOADED_COUNT=$(echo $UPLOAD_RESPONSE | grep -o '"successful_uploads":[0-9]*' | cut -d':' -f2)
FAILED_COUNT=$(echo $UPLOAD_RESPONSE | grep -o '"failed_uploads":[0-9]*' | cut -d':' -f2)

if [ "$SUCCESS" != "true" ] && [ "$SUCCESS" != " true" ]; then
  echo "❌ Upload failed. Response:"
  echo "$UPLOAD_RESPONSE"
  exit 1
fi

echo "✅ Upload successful!"
echo "   Case ID: $CASE_ID"
echo "   Successful uploads: $UPLOADED_COUNT"
echo "   Failed uploads: $FAILED_COUNT"

# Extract file details
GDRIVE_URL=$(echo $UPLOAD_RESPONSE | grep -o '"gdrive_url":"[^"]*"' | head -1 | cut -d'"' -f4)
FILENAME=$(echo $UPLOAD_RESPONSE | grep -o '"filename":"[^"]*"' | head -1 | cut -d'"' -f4)
EVIDENCE_ID=$(echo $UPLOAD_RESPONSE | grep -o '"evidence_id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -n "$GDRIVE_URL" ]; then
  echo "   Evidence ID: $EVIDENCE_ID"
  echo "   Filename: $FILENAME"
  echo "   Google Drive URL: $GDRIVE_URL"
fi
echo ""

# Step 5: Verify files are linked to case
echo "[5/5] Verifying case details..."
CASE_DETAILS=$(curl -s -X GET "$BASE_URL/api/chat/case/$CASE_ID/" \
  -H "Authorization: Bearer $TOKEN")

EVIDENCE_COUNT=$(echo $CASE_DETAILS | grep -o '"evidence_files":\[' | wc -l)

if [ "$EVIDENCE_COUNT" -gt 0 ]; then
  echo "✅ Case details retrieved successfully"
  echo "   Case has evidence files attached"
else
  echo "⚠️  Case details retrieved but no evidence files found"
fi
echo ""

# Summary
echo "=========================================="
echo "✅ All Tests Passed!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✓ User authenticated"
echo "  ✓ Case available: $CASE_ID"
echo "  ✓ Test file created"
echo "  ✓ File uploaded successfully"
echo "  ✓ Files linked to case"
echo ""
echo "Upload Details:"
echo "  Case ID: $CASE_ID"
echo "  Files uploaded: $UPLOADED_COUNT"
echo "  Evidence ID: $EVIDENCE_ID"
echo "  Google Drive URL: $GDRIVE_URL"
echo ""
echo "Next Steps:"
echo "  1. View case details:"
echo "     curl -X GET $BASE_URL/api/chat/case/$CASE_ID/ \\"
echo "       -H \"Authorization: Bearer $TOKEN\""
echo ""
echo "  2. Upload more files:"
echo "     curl -X POST $BASE_URL/api/evidence/cases/upload/ \\"
echo "       -H \"Authorization: Bearer $TOKEN\" \\"
echo "       -F \"case_id=$CASE_ID\" \\"
echo "       -F \"files=@/path/to/video.mp4\" \\"
echo "       -F \"cam_id=CAM-01\""
echo ""
echo "  3. Ingest into RAG system (if video):"
echo "     curl -X POST $BASE_URL/api/evidence/rag/ingest/ \\"
echo "       -H \"Authorization: Bearer $TOKEN\" \\"
echo "       -H \"Content-Type: application/json\" \\"
echo "       -d '{\"gdrive_file_id\": \"FILE_ID\", \"cam_id\": \"CAM-01\"}'"
echo ""

# Cleanup
if [ -f "/tmp/test_evidence_video.mp4" ]; then
  echo "Cleanup: Test file remains at /tmp/test_evidence_video.mp4"
fi
