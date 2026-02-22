# Frontend Chat Response Format

## Overview

The Case Chat API (`GET /api/chat/case/{case_id}/`) returns a frontend-compatible response format with role-based messages and media attachments, matching the requirements for the EvidenceTrace.AI chat interface.

## Response Structure

### Complete Response Example

```json
{
  "case_id": "699a806661a8bbaa3a3e03e6",
  "case_name": "State v. Anderson - Robbery Investigation",
  "case_description": "A high-profile case involving allegations of armed robbery and digital evidence tampering.",
  "total_evidence_files": 2,
  "evidence_files": [
    {
      "type": "video",
      "url": "https://drive.google.com/file/d/1ABC123XYZ/view",
      "description": "camera_01_footage.mp4",
      "filename": "camera_01_footage.mp4",
      "file_size": 15728640,
      "upload_date": "2026-02-20T10:30:00Z"
    },
    {
      "type": "image",
      "url": "https://drive.google.com/file/d/1DEF456GHI/view",
      "description": "suspect_screenshot.jpg",
      "filename": "suspect_screenshot.jpg",
      "file_size": 2048576,
      "upload_date": "2026-02-20T11:15:00Z"
    }
  ],
  "messages": [
    {
      "id": "60f1e2d3c4b5a6e7f8g9h0i1",
      "role": "assistant",
      "content": "Hello, I'm your AI Evidence Assistant. I've analyzed all uploaded evidence files. Ask me anything about the case.",
      "timestamp": "2026-02-22T14:34:00Z",
      "media": []
    },
    {
      "id": "60f1e2d3c4b5a6e7f8g9h0i2",
      "role": "user",
      "content": "What happened between 3:15 PM and 3:30 PM on February 14th?",
      "timestamp": "2026-02-22T14:35:00Z",
      "media": []
    },
    {
      "id": "60f1e2d3c4b5a6e7f8g9h0i3",
      "role": "assistant",
      "content": "Based on the evidence, at 3:18 PM, a black sedan was observed entering the parking lot from the north entrance. At 3:22 PM, two individuals exited the vehicle and approached the building entrance. The security camera footage shows clear visibility of both subjects.",
      "timestamp": "2026-02-22T14:35:05Z",
      "media": []
    },
    {
      "id": "60f1e2d3c4b5a6e7f8g9h0i4",
      "role": "user",
      "content": "What are the potential legal implications of the evidence presented?",
      "timestamp": "2026-02-22T14:40:00Z",
      "media": []
    },
    {
      "id": "60f1e2d3c4b5a6e7f8g9h0i5",
      "role": "assistant",
      "content": "The evidence presented could lead to several legal implications, including charges of armed robbery, data theft, and possibly conspiracy if others are found to be involved. The strength of the digital evidence, such as the camera footage and witness testimony, will play a crucial role in determining the outcome of the case. Additionally, if any evidence is found to have been tampered with, it could lead to further charges and complications in the legal proceedings.",
      "timestamp": "2026-02-22T14:40:08Z",
      "media": []
    }
  ]
}
```

## Field Descriptions

### Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `case_id` | string | Unique identifier for the case |
| `case_name` | string | Case title/name (e.g., "State v. Anderson") |
| `case_description` | string | Detailed case description |
| `total_evidence_files` | integer | Total number of evidence files uploaded |
| `evidence_files` | array | Array of all evidence files for this case |
| `messages` | array | Array of chat messages in chronological order |

### Evidence File Object

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Media type: "video" or "image" |
| `url` | string | Google Drive URL or file path |
| `description` | string | File description (usually filename) |
| `filename` | string | Original filename |
| `file_size` | integer | File size in bytes |
| `upload_date` | string | Upload timestamp in ISO 8601 format |

### Message Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique message identifier |
| `role` | string | Message role: "user" or "assistant" |
| `content` | string | Message text content |
| `timestamp` | string | Message timestamp in ISO 8601 format |
| `media` | array | Array of media items attached to this message |

### Media Item Object (Future Enhancement)

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Media type: "image" or "video" |
| `url` | string | URL to the media file |
| `description` | string | Description of the media |
| `filename` | string | Original filename |
| `file_size` | integer | File size in bytes |
| `upload_date` | string | Upload timestamp |

## Message Roles

### "user" Role
- Messages sent by investigators/users
- Questions, queries, and user input
- Displayed on the right side (dark background in UI)

### "assistant" Role
- Automated responses from the AI system
- RAG query results
- Analysis summaries
- Displayed on the left side (light background in UI)

### "system" Role (Optional)
- System notifications
- Status updates
- Usually displayed in a neutral color or style

## API Usage

### Get Case Chat History

```bash
curl -X GET http://localhost:8000/api/chat/case/{case_id}/ \
  -H "Authorization: Bearer {access_token}"
```

### Send User Message

```bash
curl -X POST http://localhost:8000/api/chat/case/{case_id}/message/ \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your message here",
    "message_type": "user"
  }'
```

### Query RAG System (Auto-stored as Assistant Message)

```bash
curl -X POST http://localhost:8000/api/evidence/rag/query/ \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "{case_id}",
    "query": "Find person in red jacket",
    "top_k": 10
  }'
```

## Frontend Integration

### React/JavaScript Example

```javascript
// Fetch case chat history
const fetchCaseChat = async (caseId, token) => {
  const response = await fetch(
    `http://localhost:8000/api/chat/case/${caseId}/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const data = await response.json();
  return data;
};

// Usage
const chatData = await fetchCaseChat('699a806661a8bbaa3a3e03e6', accessToken);

console.log('Case:', chatData.case_name);
console.log('Messages:', chatData.messages.length);

// Display messages
chatData.messages.forEach(msg => {
  if (msg.role === 'user') {
    // Render user message (right side, dark)
    console.log(`User: ${msg.content}`);
  } else if (msg.role === 'assistant') {
    // Render assistant message (left side, light)
    console.log(`AI: ${msg.content}`);
  }
});

// Display evidence files
chatData.evidence_files.forEach(file => {
  console.log(`Evidence: ${file.filename} (${file.type})`);
  console.log(`  URL: ${file.url}`);
});
```

### TypeScript Interface

```typescript
interface MediaItem {
  type: 'image' | 'video';
  url: string;
  description: string;
  filename: string;
  file_size: number;
  upload_date: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  media: MediaItem[];
}

interface CaseChatResponse {
  case_id: string;
  case_name: string;
  case_description: string;
  total_evidence_files: number;
  evidence_files: MediaItem[];
  messages: Message[];
}
```

## Message Flow

### 1. User Opens Case
```
GET /api/chat/case/{case_id}/
→ Returns case details + all messages + evidence files
```

### 2. User Sends Message
```
POST /api/chat/case/{case_id}/message/
{
  "content": "What happened at 3:15 PM?",
  "message_type": "user"
}
→ Message stored in database
→ Frontend refreshes chat
```

### 3. User Queries RAG System
```
POST /api/evidence/rag/query/
{
  "case_id": "{case_id}",
  "query": "Find suspect in red jacket"
}
→ RAG pipeline executes
→ User message stored with role="user"
→ AI response stored with role="assistant"
→ Frontend receives results + chat IDs
→ Frontend refreshes chat to show conversation
```

### 4. Frontend Displays Chat
```
- Group messages by role
- Apply styling:
  - user: dark background, right-aligned
  - assistant: light background, left-aligned
- Format timestamps
- Display evidence files separately or inline
```

## Best Practices

### 1. Polling for Updates
```javascript
// Poll for new messages every 5 seconds
setInterval(async () => {
  const data = await fetchCaseChat(caseId, token);
  updateChatUI(data.messages);
}, 5000);
```

### 2. WebSocket (Future Enhancement)
```javascript
// Real-time updates
const ws = new WebSocket(`ws://localhost:8000/ws/chat/${caseId}/`);
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  appendMessage(message);
};
```

### 3. Message Rendering
```javascript
const renderMessage = (message) => {
  const className = message.role === 'user' 
    ? 'message-user' 
    : 'message-assistant';
  
  return `
    <div class="${className}">
      <div class="message-content">${message.content}</div>
      <div class="message-timestamp">${formatTime(message.timestamp)}</div>
    </div>
  `;
};
```

### 4. Evidence Display
```javascript
const renderEvidence = (file) => {
  const icon = file.type === 'video' ? '🎥' : '📷';
  
  return `
    <div class="evidence-file">
      <span class="icon">${icon}</span>
      <span class="filename">${file.filename}</span>
      <a href="${file.url}" target="_blank">View</a>
    </div>
  `;
};
```

## Timestamp Formatting

All timestamps are in ISO 8601 format (`YYYY-MM-DDTHH:mm:ssZ`).

### JavaScript Formatting

```javascript
const formatTimestamp = (isoString) => {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Example: "2026-02-22T14:35:00Z" → "2:35 PM"
```

## Testing

### Test Script
```bash
cd backend
./test_chat_format.sh
```

### Manual Testing
```bash
# 1. Get access token
TOKEN=$(curl -s -X POST http://localhost:8000/api/users/signin/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access')

# 2. Get chat history
curl -X GET http://localhost:8000/api/chat/case/YOUR_CASE_ID/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq .

# 3. Verify format
# - Check for case_id, case_name, case_description
# - Check messages have role, timestamp, media fields
# - Check evidence_files array
```

## Migration Notes

### Old Format vs New Format

**Old Format (Deprecated):**
```json
{
  "case": {...},
  "chat": {...},
  "messages": [
    {
      "message_type": "user",
      "created_at": "..."
    }
  ]
}
```

**New Format (Current):**
```json
{
  "case_id": "...",
  "case_name": "...",
  "messages": [
    {
      "role": "user",
      "timestamp": "..."
    }
  ]
}
```

### Key Changes
- `message_type` → `role`
- `created_at` → `timestamp`
- Nested `case` object → Flat `case_id`, `case_name`, `case_description`
- Removed `chat` object (not needed by frontend)
- Added `media` array to each message
- Added `evidence_files` at top level with standardized format

## Support

For issues or questions about the chat format:
1. Check the test script output: `./test_chat_format.sh`
2. Verify response format matches this documentation
3. Review [README.md](../README.md) for API examples
4. Check [RAG_CHAT_INTEGRATION.md](RAG_CHAT_INTEGRATION.md) for RAG integration
