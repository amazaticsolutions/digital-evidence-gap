# RAG Data Flow: LLM Input vs Chat Storage

## Overview

This document explains how the RAG system handles data differently for LLM processing versus chat storage to optimize performance and maintain user context.

## Key Principle: Separation of Concerns

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      RAG Pipeline (9 Steps)             │
│  1. Query Validation                    │
│  2. Vector + Keyword Search             │
│  3. Temporal Expansion                  │
│  4. LLM Scoring ◄───────────────┐       │
│  5. Relevance Filtering         │       │
│  6. Metadata Enrichment         │       │
│  7. Timeline Generation         │       │
│  8. Summary Generation          │       │
└────────┬────────────────────────┴───────┘
         │                        │
         ▼                        ▼
   ┌─────────────┐      ┌──────────────────┐
   │   To LLM    │      │   To Chat DB     │
   │ (Minimal)   │      │  (Complete)      │
   └─────────────┘      └──────────────────┘
```

## What Goes to the LLM (Step 4: Scoring)

### Purpose
The LLM analyzes frame descriptions to determine relevance to user query.

### Data Sent
**Location:** `backend/multimedia_rag/query/llm_answer.py` → `_score_chunk()`

```python
# Only these fields are sent to the LLM in the prompt:
{
  "frame_id": "frame_abc123",
  "cam_id": "CAM_01",
  "timestamp": 125.5,  # seconds into video
  "caption_brief": "Person wearing red jacket",
  "caption_detailed": "A person in red outerwear walking near entrance",
  "caption_regional": "Center: person, left: door, right: wall"
}
```

### What's Excluded from LLM
❌ **Google Drive URLs** - Not needed for relevance scoring  
❌ **GPS Coordinates** - Not used in semantic analysis  
❌ **Base64 Images** - Too large, captions are sufficient  
❌ **Video IDs** - Internal references only  
❌ **User IDs** - Privacy concern  
❌ **File Paths** - No value for LLM analysis  

### Example LLM Prompt

```
You are a forensic video analyst assistant. Your task is to evaluate 
how relevant each frame description is to the user's query.

USER QUERY: Show me people wearing red jackets

Below are descriptions of video frames:

Frame 1:
  ID: frame_abc123
  Camera: CAM_01
  Timestamp: 125.5s
  Description: Person wearing red jacket | A person in red outerwear 
               walking near entrance | Center: person, left: door

Frame 2:
  ID: frame_def456
  Camera: CAM_02
  Timestamp: 230.0s
  Description: Blue car parked | Sedan in parking lot | Full frame: vehicle

[... more frames ...]

Respond ONLY with a JSON array with: frame_id, score, relevant, explanation
```

### Why This Matters
- **Performance:** Smaller prompts = faster LLM responses
- **Cost:** Fewer tokens = lower API costs (if using paid LLM)
- **Accuracy:** Focused context = better relevance scoring
- **Privacy:** No sensitive file paths or URLs exposed to LLM

## What Goes to Chat Database (Storage)

### Purpose
Preserve complete context so users can:
- View exact evidence locations (Google Drive URLs)
- Download original media files
- See GPS coordinates on maps
- Resume investigations with full context

### Data Stored
**Location:** `backend/evidence/rag_views.py` → `RAGQueryView.post()`

```python
# Complete results stored in chat message:
{
  "summary": "Found 5 frames showing people in red jackets...",
  "total_found": 5,
  "total_searched": 1000,
  "result_count": 5,
  "search_method": "combined",
  "results": [
    {
      "_id": "frame_abc123",
      "cam_id": "CAM_01",
      "timestamp": 125.5,
      "score": 95.5,
      "relevant": true,
      "explanation": "Directly matches query - clear red jacket",
      "caption_brief": "Person wearing red jacket",
      "caption_detailed": "A person in red outerwear...",
      "caption_regional": "Center: person, left: door",
      "gdrive_url": "https://drive.google.com/file/d/abc123/view",  ✅
      "gps_lat": 40.7128,  ✅
      "gps_lng": -74.0060,  ✅
      "reid_group": "person_001",  ✅
      "sequence": 125,  ✅
      "source": "CAM_01_video"  ✅
    },
    // ... more results
  ],
  "timeline": [
    // Chronological view of same results
  ]
}
```

### What's Included in Chat Storage
✅ **Google Drive URLs** - For downloading/viewing evidence  
✅ **GPS Coordinates** - For mapping and location analysis  
✅ **ReID Groups** - Person tracking across frames  
✅ **Scores & Explanations** - LLM's relevance analysis  
✅ **Full Captions** - All three caption levels  
✅ **Timeline Data** - Chronological organization  
✅ **Search Metadata** - Method used, queries, counts  

### Example Chat Message (MongoDB Document)

```json
{
  "_id": "msg_60f1e2d3c4b5a6e7",
  "chat_id": "chat_abc123",
  "user_id": 42,
  "message_type": "assistant",
  "content": "{\"summary\": \"Found 5 frames...\", \"results\": [...]}",
  "created_at": "2026-02-22T14:30:00Z"
}
```

When user retrieves chat history:
```bash
GET /api/chat/case/{case_id}/
```

They get the complete results with Google Drive URLs for downloading evidence.

## Data Flow Example

### Step-by-Step

#### 1. User Sends Query
```bash
POST /api/evidence/rag/query/
{
  "case_id": "case_123",
  "query": "Show me people wearing red jackets",
  "top_k": 5
}
```

#### 2. Pipeline Searches Database
Retrieves frames from MongoDB with all metadata:
```python
frames = [
  {
    "_id": "frame_abc123",
    "cam_id": "CAM_01",
    "timestamp": 125.5,
    "caption_brief": "Person wearing red jacket",
    "gdrive_url": "https://drive.google.com/...",  # Has URL
    "gps_lat": 40.7128,
    # ... all fields
  }
]
```

#### 3. LLM Scoring (Minimal Data)
```python
# Only sends to LLM:
prompt = f"""
Frame 1:
  ID: frame_abc123
  Camera: CAM_01
  Timestamp: 125.5s
  Description: Person wearing red jacket
"""
# NO Google Drive URL sent!
```

#### 4. LLM Returns Scores
```json
{
  "frame_id": "frame_abc123",
  "score": 95.5,
  "relevant": true,
  "explanation": "Directly matches query"
}
```

#### 5. Merge Scores with Full Data
```python
# Combine LLM scores with original data
enriched_results = [
  {
    "_id": "frame_abc123",
    "score": 95.5,  # From LLM
    "relevant": true,  # From LLM
    "explanation": "...",  # From LLM
    "gdrive_url": "https://drive.google.com/...",  # Original data
    "gps_lat": 40.7128,  # Original data
    # ... all original fields preserved
  }
]
```

#### 6. Store in Chat (Complete Data)
```python
chat_message = {
  "summary": "Found 5 frames...",
  "results": enriched_results,  # Includes gdrive_url!
  "timeline": timeline_results   # Also includes gdrive_url!
}
```

#### 7. Return to User (Complete Data)
```json
{
  "summary": "Found 5 frames showing people in red jackets",
  "results": [
    {
      "_id": "frame_abc123",
      "gdrive_url": "https://drive.google.com/file/d/abc123/view",
      "score": 95.5,
      // ... all fields
    }
  ]
}
```

## Code Locations

### LLM Input (Minimal)
```
backend/multimedia_rag/query/llm_answer.py
  └─ _score_chunk() function
     └─ Lines 220-245 (prompt construction)
        # Only includes: frame_id, cam_id, timestamp, captions
```

### Chat Storage (Complete)
```
backend/evidence/rag_views.py
  └─ RAGQueryView.post() method
     └─ Lines 280-295 (response construction)
        # Includes: summary, results[], timeline[]
        # Each result has: gdrive_url, GPS, reid_group, etc.
```

### Result Formatting
```
backend/multimedia_rag/query/pipeline.py
  └─ format_results_for_display() function
     └─ Lines 341-385 (_clean helper)
        # Preserves: gdrive_url, gps_lat, gps_lng, reid_group
```

## Verification

### Test LLM Input (Should NOT have URLs)

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run query
curl -X POST http://localhost:8000/api/evidence/rag/query/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"case_id":"abc123","query":"test"}'

# Check logs - LLM prompt should NOT show gdrive_url
tail -f backend/logs/debug.log | grep "Prompt:"
```

### Test Chat Storage (Should HAVE URLs)

```bash
# Send RAG query
curl -X POST http://localhost:8000/api/evidence/rag/query/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "case_id": "abc123",
    "query": "Show me red jackets",
    "top_k": 5
  }'

# Get chat history
curl -X GET http://localhost:8000/api/chat/case/abc123/ \
  -H "Authorization: Bearer $TOKEN" | jq '.messages[-1].content' | jq '.results[].gdrive_url'

# Should output Google Drive URLs:
# "https://drive.google.com/file/d/abc123/view"
# "https://drive.google.com/file/d/def456/view"
```

## Benefits of This Approach

### 1. Performance
- **Faster LLM responses:** Smaller prompts process quicker
- **Lower token usage:** Less data = fewer tokens
- **Reduced costs:** Important for paid LLM APIs

### 2. Security & Privacy
- **No sensitive URLs to LLM:** File paths stay internal
- **Controlled data exposure:** LLM only sees necessary context
- **Audit trail:** Full data in chat for compliance

### 3. User Experience
- **Complete context:** Users see all relevant file paths
- **Downloadable evidence:** Google Drive URLs for file access
- **Rich metadata:** GPS, ReID, timeline data preserved

### 4. Maintainability
- **Clear separation:** LLM logic vs storage logic
- **Easy debugging:** Can inspect what LLM sees vs what's stored
- **Flexible updates:** Can change LLM prompt without affecting storage

## Common Questions

### Q: Why not send everything to the LLM?
**A:** LLMs work better with focused, relevant data. URLs and GPS coordinates don't help with semantic relevance scoring. Including them:
- Wastes tokens (increases cost)
- Adds noise to the prompt
- Slows down processing
- No benefit to accuracy

### Q: What if I need the LLM to see file paths?
**A:** In forensic analysis, the LLM's job is to evaluate **content relevance**, not manage files. File paths are for:
- User download/viewing
- System record-keeping
- Audit trails

Not for LLM semantic analysis.

### Q: How do users access the media files?
**A:** They retrieve the chat history which includes Google Drive URLs:
```bash
GET /api/chat/case/{case_id}/
```
Response includes full results with `gdrive_url` field.

### Q: Can I include images in chat storage?
**A:** Yes, but it's disabled by default:
```python
api_results = format_results_for_display(results, include_images=True)
```
This adds `image_base64` to results. Warning: Large data!

## Summary

| Data Field | Sent to LLM? | Stored in Chat? | Why? |
|------------|--------------|-----------------|------|
| Frame ID | ✅ Yes | ✅ Yes | Needed for scoring reference |
| Camera ID | ✅ Yes | ✅ Yes | Context for scene understanding |
| Timestamp | ✅ Yes | ✅ Yes | Temporal context |
| Captions | ✅ Yes | ✅ Yes | Core content for relevance |
| **Google Drive URL** | ❌ No | ✅ Yes | **User needs for download, not for LLM** |
| GPS Coordinates | ❌ No | ✅ Yes | User needs for mapping |
| ReID Group | ❌ No | ✅ Yes | Person tracking across frames |
| Score | ❌ No | ✅ Yes | Generated BY the LLM |
| Explanation | ❌ No | ✅ Yes | Generated BY the LLM |
| Image Base64 | ❌ No | ❌ No* | Too large (*optional) |

## Best Practices

1. **Keep LLM prompts minimal** - Only send data needed for scoring
2. **Store complete results** - Users need full context later
3. **Document data flow** - Clear separation of concerns
4. **Test both paths** - Verify LLM input AND chat storage
5. **Monitor token usage** - Track costs if using paid LLM

## Related Documentation

- [RAG_CHAT_INTEGRATION.md](RAG_CHAT_INTEGRATION.md) - How RAG integrates with chat
- [CHAT_RESUMPTION_GUIDE.md](CHAT_RESUMPTION_GUIDE.md) - Accessing stored chat data
- [MULTIMEDIA_RAG_API.md](MULTIMEDIA_RAG_API.md) - API endpoints and usage
- [backend/multimedia_rag/README.md](multimedia_rag/README.md) - RAG pipeline overview
