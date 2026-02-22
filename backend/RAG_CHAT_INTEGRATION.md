# RAG Query with Chat Storage Integration

## Overview

All RAG queries are now automatically stored in the case chat history. This allows you to:
- View past queries and responses in the "Past Cases" interface
- Maintain a conversation history for each case
- Track what questions have been asked about the evidence
- Share investigation findings with team members

## How It Works

When you query the RAG system via `/api/evidence/rag/query/`, the following happens:

1. **Query Validation**: The system verifies the case exists and you own it
2. **Chat Creation**: If a chat doesn't exist for the case, one is created automatically
3. **User Message**: Your query is saved as a "user" message in the chat
4. **RAG Processing**: The 9-step RAG pipeline executes to find relevant frames
5. **Assistant Response**: The results summary is saved as an "assistant" message
6. **Response**: You receive the results plus chat metadata (chat_id, message IDs)

## API Endpoint

### POST /api/evidence/rag/query/

Query the RAG system with natural language. Requires authentication.

**Request Body:**
```json
{
  "case_id": "699a806661a8bbaa3a3e03e6",
  "query": "Show me all frames with a person wearing red clothing",
  "top_k": 10,
  "enable_reid": false,
  "filters": {
    "video_id": "VIDEO-123",
    "cam_id": "CAM-01"
  }
}
```

**Request Fields:**
- `case_id` (string, required): ID of the case to query
- `query` (string, required): Natural language query
- `top_k` (integer, optional): Maximum results to return (1-100, default: 10)
- `enable_reid` (boolean, optional): Enable person re-identification (default: false)
- `filters` (object, optional): Additional filtering
  - `video_id`: Filter by specific video
  - `cam_id`: Filter by specific camera

**Response:**
```json
{
  "chat_id": "60f1e2d3c4b5a6e7f8g9h0i1",
  "user_message_id": "60f1e2d3c4b5a6e7f8g9h0i2",
  "assistant_message_id": "60f1e2d3c4b5a6e7f8g9h0i3",
  "query": "Show me all frames with a person wearing red clothing",
  "total_searched": 150,
  "total_found": 12,
  "summary": "Found 12 frames showing individuals in red clothing across 3 cameras...",
  "results": [
    {
      "id": "frame_001",
      "video_id": "VIDEO-123",
      "cam_id": "CAM-01",
      "timestamp": 45.2,
      "score": 95.5,
      "relevant": true,
      "explanation": "Person wearing red jacket clearly visible in center frame",
      "caption": "A person in red jacket standing near a vehicle",
      "gps_lat": 40.7128,
      "gps_lng": -74.0060,
      "reid_group": null,
      "gdrive_url": "https://drive.google.com/file/d/...",
      "confidence": 0.92
    }
  ],
  "timeline": [...],
  "search_method": "hybrid",
  "queries_used": ["person wearing red clothing", "individual in red attire"],
  "reid_warning": null
}
```

## Complete Workflow Example

### 1. Create a User (if not exists)
```bash
curl -X POST http://localhost:8000/api/users/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "investigator@police.gov",
    "password": "SecurePassword123!",
    "full_name": "Jane Investigator"
  }'
```

### 2. Sign In
```bash
curl -X POST http://localhost:8000/api/users/signin/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "investigator@police.gov",
    "password": "SecurePassword123!"
  }'
```

**Save the access token from the response:**
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Create a Case
```bash
curl -X POST http://localhost:8000/api/search/cases/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Downtown Theft Investigation",
    "description": "Investigating theft at downtown mall on Feb 20, 2026",
    "query_text": "Find suspect in red jacket"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Case created successfully",
  "case": {
    "id": "699a806661a8bbaa3a3e03e6",
    "case_id": "CASE-ABC123",
    "title": "Downtown Theft Investigation",
    ...
  }
}
```

**Save the case ID:**
```bash
export CASE_ID="699a806661a8bbaa3a3e03e6"
```

### 4. Upload Evidence (Google Drive)
```bash
curl -X POST http://localhost:8000/api/evidence/gdrive/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "'$CASE_ID'",
    "gdrive_url": "https://drive.google.com/file/d/1ABC123XYZ/view",
    "filename": "camera_01_footage.mp4",
    "media_type": "video",
    "cam_id": "CAM-01",
    "gps_lat": 40.7128,
    "gps_lng": -74.0060
  }'
```

### 5. Ingest Video into RAG System
```bash
curl -X POST http://localhost:8000/api/evidence/rag/ingest/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "gdrive_file_id": "1ABC123XYZ",
    "cam_id": "CAM-01",
    "gps_lat": 40.7128,
    "gps_lng": -74.0060
  }'
```

### 6. Query the RAG System (Stores in Chat)
```bash
curl -X POST http://localhost:8000/api/evidence/rag/query/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "'$CASE_ID'",
    "query": "Show me all frames with a person wearing red clothing",
    "top_k": 10,
    "enable_reid": false
  }'
```

### 7. View Chat History for Case
```bash
curl -X GET http://localhost:8000/api/chat/case/$CASE_ID/ \
  -H "Authorization: Bearer $TOKEN"
```

**Response shows chat with all messages:**
```json
{
  "case": {
    "id": "699a806661a8bbaa3a3e03e6",
    "title": "Downtown Theft Investigation",
    ...
  },
  "chat": {
    "id": "60f1e2d3c4b5a6e7f8g9h0i1",
    "case_id": "699a806661a8bbaa3a3e03e6",
    "title": "Downtown Theft Investigation",
    "created_at": "2026-02-20T10:30:00Z",
    "updated_at": "2026-02-20T11:45:00Z"
  },
  "messages": [
    {
      "id": "60f1e2d3c4b5a6e7f8g9h0i2",
      "chat_id": "60f1e2d3c4b5a6e7f8g9h0i1",
      "user_id": 1,
      "content": "Show me all frames with a person wearing red clothing",
      "message_type": "user",
      "created_at": "2026-02-20T11:45:00Z"
    },
    {
      "id": "60f1e2d3c4b5a6e7f8g9h0i3",
      "chat_id": "60f1e2d3c4b5a6e7f8g9h0i1",
      "user_id": 1,
      "content": "{\"summary\": \"Found 12 frames...\", \"total_found\": 12, ...}",
      "message_type": "assistant",
      "created_at": "2026-02-20T11:45:05Z"
    }
  ],
  "evidence_files": [...]
}
```

### 8. Send Additional Messages to Case Chat
```bash
curl -X POST http://localhost:8000/api/chat/case/$CASE_ID/message/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Great! Can you focus on cameras near the entrance?",
    "message_type": "user"
  }'
```

## Frontend Integration

The "Past Cases" view can now display:
1. Case summary (title, evidence count, created date)
2. Chat conversation history (all queries and responses)
3. Evidence files linked to the case

### Getting All Cases with Chat Summary
```bash
curl -X GET "http://localhost:8000/api/search/cases/summary/?status=completed" \
  -H "Authorization: Bearer $TOKEN"
```

### For Each Case, Get Full Details
```bash
curl -X GET http://localhost:8000/api/chat/case/$CASE_ID/ \
  -H "Authorization: Bearer $TOKEN"
```

## Message Types

The chat system supports three message types:

1. **user**: Messages from the investigator (queries, notes)
2. **assistant**: Automated responses from the RAG system
3. **system**: System notifications (case status changes, etc.)

## Benefits

### For Investigators
- Complete audit trail of all queries
- Easy review of past findings
- Collaborative investigation support
- Context preservation

### For Management
- Track investigation progress
- Review query patterns
- Quality assurance
- Performance metrics

### For Legal/Court
- Documented evidence discovery process
- Timestamp verification
- Chain of custody support
- Reproducible results

## Best Practices

1. **Be Specific**: Ask clear, specific questions for better results
2. **Use Filters**: Narrow down by camera, video, or time when needed
3. **Enable ReID**: When tracking suspects across multiple cameras
4. **Review Timeline**: Check both relevance-sorted and time-sorted results
5. **Check Summary**: Read the LLM-generated summary for quick insights

## Troubleshooting

### Query Returns No Results
- Check that videos have been ingested via `/api/evidence/rag/ingest/`
- Verify embeddings exist using `/api/evidence/rag/stats/`
- Try more general queries
- Check filter parameters

### Case Not Found Error
- Verify case_id is correct
- Ensure you own the case
- Check authentication token is valid

### Chat Not Created
- Usually auto-created on first query
- Can manually create via `/api/chat/case/{case_id}/message/`
- Check case exists first

## Related Endpoints

- `POST /api/evidence/rag/ingest/` - Ingest video into RAG
- `GET /api/evidence/rag/stats/` - Get RAG system statistics
- `GET /api/chat/case/{case_id}/` - Get case chat details
- `POST /api/chat/case/{case_id}/message/` - Send message to case
- `GET /api/search/cases/summary/` - List all cases

## Technical Details

### Storage
- **Cases**: MongoDB `searches` collection
- **Chats**: MongoDB `chats` collection  
- **Messages**: MongoDB `messages` collection
- **Frames**: MongoDB `frames` collection

### Performance
- First query typically takes 3-5 seconds (LLM processing)
- Subsequent queries are faster (cached embeddings)
- ReID adds ~1-2 seconds per query
- Chat storage is async and doesn't impact query speed

### Limitations
- Maximum 100 results per query (use top_k parameter)
- ReID works best with clear frontal views
- LLM requires Ollama server running
- Vector search requires MongoDB Atlas or local vector index
