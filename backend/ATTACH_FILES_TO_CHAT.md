# Attaching Google Drive Files to Chat Messages

## Overview

You can attach Google Drive file paths (and other media) to chat messages using the `media` array field. This allows you to associate uploaded evidence files with specific messages in a conversation.

## Complete Workflow

### Step 1: Upload Files to Case

First, upload files to Google Drive and link them to the case:

```bash
curl -X POST http://localhost:8000/api/evidence/cases/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "case_id=abc123" \
  -F "files=@video1.mp4" \
  -F "files=@image1.jpg"
```

**Response:**
```json
{
  "case_id": "abc123",
  "case_title": "Bank Robbery Investigation",
  "uploaded_files": [
    {
      "filename": "video1.mp4",
      "gdrive_url": "https://drive.google.com/file/d/abc123xyz/view",
      "evidence_id": "evidence_001",
      "file_size": 15728640,
      "media_type": "video"
    },
    {
      "filename": "image1.jpg",
      "gdrive_url": "https://drive.google.com/file/d/def456ghi/view",
      "evidence_id": "evidence_002",
      "file_size": 2048576,
      "media_type": "image"
    }
  ],
  "failed_files": []
}
```

### Step 2: Send Message with Attached Files

Send a chat message with the Google Drive URLs attached:

```bash
curl -X POST http://localhost:8000/api/chat/case/abc123/message/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I uploaded surveillance footage from the bank",
    "message_type": "user",
    "media": [
      {
        "type": "video",
        "url": "https://drive.google.com/file/d/abc123xyz/view",
        "filename": "video1.mp4",
        "description": "Bank entrance camera footage",
        "file_size": 15728640,
        "evidence_id": "evidence_001"
      },
      {
        "type": "image",
        "url": "https://drive.google.com/file/d/def456ghi/view",
        "filename": "image1.jpg",
        "description": "Suspect screenshot",
        "file_size": 2048576,
        "evidence_id": "evidence_002"
      }
    ]
  }'
```

**Response:**
```json
{
  "id": "msg_60f1e2d3c4b5a6e7",
  "chat_id": "chat_abc123",
  "user_id": 42,
  "content": "I uploaded surveillance footage from the bank",
  "message_type": "user",
  "created_at": "2026-02-22T15:30:00Z",
  "media": [
    {
      "type": "video",
      "url": "https://drive.google.com/file/d/abc123xyz/view",
      "filename": "video1.mp4",
      "description": "Bank entrance camera footage",
      "file_size": 15728640,
      "evidence_id": "evidence_001"
    },
    {
      "type": "image",
      "url": "https://drive.google.com/file/d/def456ghi/view",
      "filename": "image1.jpg",
      "description": "Suspect screenshot",
      "file_size": 2048576,
      "evidence_id": "evidence_002"
    }
  ]
}
```

### Step 3: Retrieve Messages with Attachments

Get chat history to see messages with their attached files:

```bash
curl -X GET http://localhost:8000/api/chat/case/abc123/ \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "case_id": "abc123",
  "case_name": "Bank Robbery Investigation",
  "case_description": "Investigation of robbery at Main Street Bank",
  "total_evidence_files": 2,
  "evidence_files": [
    {
      "type": "video",
      "url": "https://drive.google.com/file/d/abc123xyz/view",
      "description": "video1.mp4",
      "filename": "video1.mp4",
      "file_size": 15728640,
      "upload_date": "2026-02-22T14:00:00Z"
    },
    {
      "type": "image",
      "url": "https://drive.google.com/file/d/def456ghi/view",
      "description": "image1.jpg",
      "filename": "image1.jpg",
      "file_size": 2048576,
      "upload_date": "2026-02-22T14:00:00Z"
    }
  ],
  "messages": [
    {
      "id": "msg_60f1e2d3c4b5a6e7",
      "role": "user",
      "content": "I uploaded surveillance footage from the bank",
      "timestamp": "2026-02-22T15:30:00Z",
      "media": [
        {
          "type": "video",
          "url": "https://drive.google.com/file/d/abc123xyz/view",
          "filename": "video1.mp4",
          "description": "Bank entrance camera footage",
          "file_size": 15728640,
          "evidence_id": "evidence_001"
        },
        {
          "type": "image",
          "url": "https://drive.google.com/file/d/def456ghi/view",
          "filename": "image1.jpg",
          "description": "Suspect screenshot",
          "file_size": 2048576,
          "evidence_id": "evidence_002"
        }
      ]
    }
  ]
}
```

## Media Object Structure

Each item in the `media` array should have:

```typescript
interface MediaAttachment {
  type: "video" | "image" | "document";  // Media type
  url: string;                            // Google Drive URL or file path
  filename?: string;                      // Original filename
  description?: string;                   // Description of the file
  file_size?: number;                     // File size in bytes
  evidence_id?: string;                   // Reference to evidence ID
  upload_date?: string;                   // ISO 8601 timestamp
}
```

## Use Cases

### Use Case 1: Upload and Immediately Share

```javascript
// 1. Upload files
const uploadResponse = await fetch('/api/evidence/cases/upload/', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

const { uploaded_files } = await uploadResponse.json();

// 2. Send message with uploaded files attached
const media = uploaded_files.map(file => ({
  type: file.media_type,
  url: file.gdrive_url,
  filename: file.filename,
  file_size: file.file_size,
  evidence_id: file.evidence_id
}));

await fetch(`/api/chat/case/${caseId}/message/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    content: 'Here are the new evidence files',
    message_type: 'user',
    media: media
  })
});
```

### Use Case 2: Reference Existing Evidence

```javascript
// Reference previously uploaded files
await fetch(`/api/chat/case/${caseId}/message/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    content: 'Please review the camera footage from yesterday',
    message_type: 'user',
    media: [
      {
        type: 'video',
        url: 'https://drive.google.com/file/d/existing_file/view',
        filename: 'camera_01_footage.mp4',
        description: 'Entrance camera from Feb 21'
      }
    ]
  })
});
```

### Use Case 3: RAG Query Results with Frame Links

```javascript
// After RAG query, attach specific frames to a message
const ragResponse = await fetch('/api/evidence/rag/query/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    case_id: caseId,
    query: 'Show me red jackets',
    top_k: 5
  })
});

const { results } = await ragResponse.json();

// Extract frame URLs and attach to a summary message
const frameMedia = results.map(frame => ({
  type: 'image',
  url: frame.gdrive_url,
  filename: `frame_${frame._id}.jpg`,
  description: frame.caption_brief,
  timestamp: frame.timestamp
}));

await fetch(`/api/chat/case/${caseId}/message/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    content: 'Found 5 frames showing people in red jackets',
    message_type: 'user',
    media: frameMedia
  })
});
```

## Frontend Implementation

### React Example

```javascript
import React, { useState } from 'react';

function ChatMessage({ message }) {
  return (
    <div className={`message ${message.role}`}>
      <div className="message-content">{message.content}</div>
      
      {message.media && message.media.length > 0 && (
        <div className="message-attachments">
          <h4>Attachments:</h4>
          {message.media.map((item, index) => (
            <div key={index} className="attachment">
              {item.type === 'video' && (
                <a href={item.url} target="_blank" rel="noopener noreferrer">
                  🎥 {item.filename || 'Video'}
                </a>
              )}
              {item.type === 'image' && (
                <a href={item.url} target="_blank" rel="noopener noreferrer">
                  🖼️ {item.filename || 'Image'}
                </a>
              )}
              <div className="attachment-details">
                {item.description && <p>{item.description}</p>}
                {item.file_size && (
                  <span>{(item.file_size / 1024 / 1024).toFixed(2)} MB</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      <div className="message-timestamp">
        {new Date(message.timestamp).toLocaleString()}
      </div>
    </div>
  );
}

function SendMessageForm({ caseId, onMessageSent }) {
  const [content, setContent] = useState('');
  const [attachments, setAttachments] = useState([]);

  const handleUpload = async (files) => {
    const formData = new FormData();
    formData.append('case_id', caseId);
    files.forEach(file => formData.append('files', file));

    const response = await fetch('/api/evidence/cases/upload/', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });

    const { uploaded_files } = await response.json();
    
    const media = uploaded_files.map(file => ({
      type: file.media_type,
      url: file.gdrive_url,
      filename: file.filename,
      file_size: file.file_size,
      evidence_id: file.evidence_id
    }));

    setAttachments([...attachments, ...media]);
  };

  const handleSend = async () => {
    await fetch(`/api/chat/case/${caseId}/message/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content,
        message_type: 'user',
        media: attachments
      })
    });

    setContent('');
    setAttachments([]);
    onMessageSent();
  };

  return (
    <div className="send-message-form">
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Type your message..."
      />
      
      <input
        type="file"
        multiple
        onChange={(e) => handleUpload(Array.from(e.target.files))}
      />

      {attachments.length > 0 && (
        <div className="pending-attachments">
          <h4>Attachments to send:</h4>
          {attachments.map((item, index) => (
            <div key={index}>
              {item.filename} ({(item.file_size / 1024 / 1024).toFixed(2)} MB)
            </div>
          ))}
        </div>
      )}

      <button onClick={handleSend}>Send</button>
    </div>
  );
}
```

## Benefits

✅ **Context Preservation:** Link evidence to specific conversations  
✅ **Easy Access:** One-click access to Google Drive files from chat  
✅ **Timeline Tracking:** See when files were shared in investigation  
✅ **Collaboration:** Team members see which files were discussed  
✅ **Audit Trail:** Complete record of evidence sharing  

## API Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/evidence/cases/upload/` | POST | Upload files to Google Drive |
| `/api/chat/case/{case_id}/message/` | POST | Send message with media attachments |
| `/api/chat/case/{case_id}/` | GET | Retrieve messages with attachments |

## Notes

- **Media array is optional:** You can send messages without attachments
- **Flexible structure:** Media objects can include any additional fields
- **No file validation:** API doesn't verify URLs are valid - client's responsibility
- **Storage:** Media metadata stored in MongoDB message documents
- **Size limits:** No hard limit on media array, but keep it reasonable

## Testing

Test the complete workflow:

```bash
# 1. Upload files
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/evidence/cases/upload/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "case_id=$CASE_ID" \
  -F "files=@test.mp4")

# Extract Google Drive URL
GDRIVE_URL=$(echo $UPLOAD_RESPONSE | jq -r '.uploaded_files[0].gdrive_url')

# 2. Send message with attachment
curl -X POST "http://localhost:8000/api/chat/case/$CASE_ID/message/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"content\": \"Check out this video\",
    \"media\": [{
      \"type\": \"video\",
      \"url\": \"$GDRIVE_URL\",
      \"filename\": \"test.mp4\"
    }]
  }"

# 3. Retrieve and verify
curl -X GET "http://localhost:8000/api/chat/case/$CASE_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.messages[].media'
```

## Related Documentation

- [CASE_FILE_UPLOAD_API.md](CASE_FILE_UPLOAD_API.md) - File upload details
- [FRONTEND_CHAT_FORMAT.md](FRONTEND_CHAT_FORMAT.md) - Complete response format
- [CHAT_RESUMPTION_GUIDE.md](CHAT_RESUMPTION_GUIDE.md) - Chat workflow
