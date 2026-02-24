# Quick Reference: Google Drive URLs in RAG System

## TL;DR

✅ **Google Drive URLs are NOT sent to the LLM**  
✅ **Google Drive URLs ARE stored in chat history**  
✅ **Users can access URLs via chat API**

## How It Works

```
User Query → RAG Pipeline → Split Data:
                              ├─ To LLM: captions only (no URLs)
                              └─ To Chat DB: complete results (with URLs)
```

## The Code

### What Goes to LLM (NO URLs)
**File:** `backend/multimedia_rag/query/llm_answer.py`

```python
# Line 220-245: _score_chunk() function
prompt = f"""
Frame {i+1}:
  ID: {fid}
  Camera: {cam_id}
  Timestamp: {timestamp}s
  Description: {caption_text}
"""
# ☝️ NO gdrive_url in prompt!
```

### What Gets Stored in Chat (WITH URLs)
**File:** `backend/evidence/rag_views.py`

```python
# Line 285-295: Save assistant message
response_content = json.dumps({
    "summary": "...",
    "results": api_results.get('results', []),  # ✅ Includes gdrive_url
    "timeline": api_results.get('timeline', []),  # ✅ Includes gdrive_url
}, indent=2)
```

## Example Flow

### 1. Send Query
```bash
POST /api/evidence/rag/query/
{
  "case_id": "abc123",
  "query": "Show me red jackets",
  "top_k": 5
}
```

### 2. LLM Sees (Internal)
```
Frame 1:
  ID: frame_123
  Camera: CAM_01
  Timestamp: 125.5s
  Description: Person wearing red jacket
```
❌ **No Google Drive URL**

### 3. Chat Stores (MongoDB)
```json
{
  "message_type": "assistant",
  "content": {
    "results": [
      {
        "gdrive_url": "https://drive.google.com/file/d/abc123/view",
        "caption": "Person wearing red jacket",
        ...
      }
    ]
  }
}
```
✅ **Has Google Drive URL**

### 4. User Retrieves
```bash
GET /api/chat/case/abc123/
```
```json
{
  "messages": [
    {
      "role": "assistant",
      "content": "{\"results\": [{\"gdrive_url\": \"...\"}]}"
    }
  ]
}
```
✅ **User gets Google Drive URL**

## Verification

### Test It
```bash
cd backend
./test_rag_data_flow.sh
```

This test:
- Sends a RAG query
- Retrieves chat history
- Verifies Google Drive URLs are in chat storage
- Confirms complete metadata is preserved

### Manual Check
```bash
# 1. Send query
curl -X POST http://localhost:8000/api/evidence/rag/query/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"case_id":"abc123","query":"test","top_k":3}'

# 2. Get chat
curl -X GET http://localhost:8000/api/chat/case/abc123/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.messages[-1].content' \
  | jq '.results[].gdrive_url'

# Should output URLs:
# "https://drive.google.com/file/d/..."
```

## Why This Matters

| Concern | Solution |
|---------|----------|
| LLM token costs | URLs use tokens unnecessarily → ❌ Don't send |
| User needs files | Users need to download evidence → ✅ Store URLs |
| Performance | Large prompts slow down LLM → ❌ Keep minimal |
| Context preservation | Investigation needs complete data → ✅ Store everything |

## Fields Comparison

| Field | To LLM? | In Chat? |
|-------|---------|----------|
| frame_id | ✅ | ✅ |
| cam_id | ✅ | ✅ |
| timestamp | ✅ | ✅ |
| captions | ✅ | ✅ |
| **gdrive_url** | ❌ | ✅ |
| gps_lat/lng | ❌ | ✅ |
| reid_group | ❌ | ✅ |
| score | ❌ | ✅ |
| explanation | ❌ | ✅ |

## Related Docs

- **Full explanation:** [RAG_DATA_FLOW.md](RAG_DATA_FLOW.md)
- **Chat integration:** [RAG_CHAT_INTEGRATION.md](RAG_CHAT_INTEGRATION.md)
- **Frontend format:** [FRONTEND_CHAT_FORMAT.md](FRONTEND_CHAT_FORMAT.md)

## Quick Links

- [LLM Input Code](multimedia_rag/query/llm_answer.py#L220-L245)
- [Chat Storage Code](evidence/rag_views.py#L285-L295)
- [Result Formatting Code](multimedia_rag/query/pipeline.py#L341-L385)
