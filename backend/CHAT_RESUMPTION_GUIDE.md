# Chat Resumption & Continuation Guide

## Overview
This guide explains how to handle resuming chat sessions when users return to a case, allowing them to continue their conversation seamlessly.

## Complete Workflow

### 1. Initial Case Load
When a user opens a case for the first time OR returns to an existing case:

```bash
# Get full chat history
curl -X GET http://localhost:8000/api/chat/case/{case_id}/ \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "case_id": "abc123",
  "case_name": "Bank Robbery Investigation",
  "case_description": "Investigation of robbery at Main Street Bank",
  "total_evidence_files": 3,
  "evidence_files": [...],
  "messages": [
    {
      "id": "msg_1",
      "role": "user",
      "content": "What vehicles were seen near the bank?",
      "timestamp": "2024-01-15T10:30:00Z",
      "media": []
    },
    {
      "id": "msg_2",
      "role": "assistant",
      "content": "Based on the video evidence, I found a black sedan...",
      "timestamp": "2024-01-15T10:30:15Z",
      "media": []
    }
  ]
}
```

### 2. Chat States

#### Scenario A: New Case (No Previous Chat)
```json
{
  "case_id": "abc123",
  "case_name": "New Investigation",
  "case_description": "...",
  "total_evidence_files": 2,
  "evidence_files": [...],
  "messages": []  // Empty array - no previous conversation
}
```

**Frontend Action:** Display empty chat interface, ready for first message.

#### Scenario B: Existing Chat (Has History)
```json
{
  "case_id": "abc123",
  "case_name": "Ongoing Investigation",
  "case_description": "...",
  "total_evidence_files": 5,
  "evidence_files": [...],
  "messages": [
    // Previous conversation history
  ]
}
```

**Frontend Action:** Display all previous messages, scroll to bottom, ready for new messages.

### 3. Resuming Chat - Sending New Messages

#### Method 1: Simple Message (No RAG Query)
Use this for regular chat messages that don't require searching evidence.

```bash
curl -X POST http://localhost:8000/api/chat/case/{case_id}/message/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Thanks for the info!",
    "message_type": "user"
  }'
```

**Response:**
```json
{
  "id": "msg_123",
  "chat_id": "chat_abc",
  "user_id": 1,
  "content": "Thanks for the info!",
  "message_type": "user",
  "created_at": "2024-01-15T11:00:00Z"
}
```

#### Method 2: RAG Query (Search Evidence)
Use this when user asks questions that require searching through evidence.

```bash
curl -X POST http://localhost:8000/api/evidence/rag/query/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "abc123",
    "query": "What time did the suspect leave the building?",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "query": "What time did the suspect leave the building?",
  "results": [...],
  "chat_id": "chat_abc",
  "user_message_id": "msg_124",
  "assistant_message_id": "msg_125"
}
```

**Automatic Behavior:**
- Creates TWO messages automatically:
  1. User message with the query
  2. Assistant message with the RAG response
- Both are saved to the chat history
- Next time user loads the case, these messages appear

### 4. Frontend Implementation

#### React/Vue Example
```javascript
// 1. Load case and chat history
async function loadCase(caseId) {
  const response = await fetch(`/api/chat/case/${caseId}/`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  // Check if chat exists
  if (data.messages.length > 0) {
    console.log('Resuming existing chat with', data.messages.length, 'messages');
    // Display all previous messages
    displayMessages(data.messages);
    // Scroll to bottom to show latest messages
    scrollToBottom();
  } else {
    console.log('Starting new chat');
    // Show empty chat interface
  }
  
  return data;
}

// 2. Send new message
async function sendMessage(caseId, content) {
  const response = await fetch(`/api/chat/case/${caseId}/message/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      content: content,
      message_type: 'user'
    })
  });
  
  const newMessage = await response.json();
  
  // Add to chat UI immediately
  appendMessage({
    id: newMessage.id,
    role: 'user',
    content: newMessage.content,
    timestamp: newMessage.created_at,
    media: []
  });
  
  return newMessage;
}

// 3. Send RAG query
async function sendRAGQuery(caseId, query) {
  // Show "thinking" indicator
  showTypingIndicator();
  
  const response = await fetch('/api/evidence/rag/query/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      case_id: caseId,
      query: query,
      top_k: 5
    })
  });
  
  const result = await response.json();
  
  // Add user message
  appendMessage({
    id: result.user_message_id,
    role: 'user',
    content: query,
    timestamp: new Date().toISOString(),
    media: []
  });
  
  // Add assistant response
  appendMessage({
    id: result.assistant_message_id,
    role: 'assistant',
    content: formatRAGResponse(result.results),
    timestamp: new Date().toISOString(),
    media: []
  });
  
  hideTypingIndicator();
}

// 4. Refresh chat (polling for updates)
async function refreshChat(caseId) {
  const response = await fetch(`/api/chat/case/${caseId}/`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  // Check if new messages exist
  const currentMessageCount = getCurrentMessageCount();
  if (data.messages.length > currentMessageCount) {
    // New messages arrived - append them
    const newMessages = data.messages.slice(currentMessageCount);
    newMessages.forEach(msg => appendMessage(msg));
  }
}
```

### 5. Complete User Journey

#### Journey 1: Resume Existing Investigation
```
Day 1:
1. User creates case → GET /api/chat/case/{case_id}/ (empty messages)
2. User asks "Show me all suspects" → POST /api/evidence/rag/query/
3. User says "Thanks" → POST /api/chat/case/{case_id}/message/
4. User closes browser

Day 2:
1. User opens same case → GET /api/chat/case/{case_id}/ (returns 3 messages)
2. Frontend displays: user's question, assistant's answer, user's "Thanks"
3. User continues: "What about the vehicle?" → POST /api/evidence/rag/query/
4. Chat now has 5 messages total
```

#### Journey 2: Collaboration Between Officers
```
Officer A (Morning):
1. Creates case and asks questions → Messages saved to DB
2. Uploads new evidence → POST /api/evidence/cases/upload/

Officer B (Afternoon):
1. Opens same case → GET /api/chat/case/{case_id}/
2. Sees ALL messages from Officer A
3. Can continue the investigation with context
```

### 6. State Management Best Practices

#### Local State
```javascript
const [chatState, setChatState] = useState({
  caseId: null,
  caseName: '',
  messages: [],
  evidenceFiles: [],
  isLoading: false,
  hasMoreHistory: false
});

// On case load
const loadCaseData = async (caseId) => {
  setChatState(prev => ({ ...prev, isLoading: true }));
  
  const data = await fetch(`/api/chat/case/${caseId}/`).then(r => r.json());
  
  setChatState({
    caseId: data.case_id,
    caseName: data.case_name,
    messages: data.messages, // All previous messages
    evidenceFiles: data.evidence_files,
    isLoading: false,
    hasMoreHistory: false // Currently loads all messages
  });
};

// On new message
const appendNewMessage = (message) => {
  setChatState(prev => ({
    ...prev,
    messages: [...prev.messages, message]
  }));
};
```

### 7. Auto-Refresh Strategies

#### Option A: Polling (Simple)
```javascript
// Poll every 5 seconds for new messages
useEffect(() => {
  const interval = setInterval(() => {
    if (caseId) {
      refreshChat(caseId);
    }
  }, 5000);
  
  return () => clearInterval(interval);
}, [caseId]);
```

#### Option B: Refresh on Focus (Efficient)
```javascript
// Refresh when user returns to tab
useEffect(() => {
  const handleFocus = () => {
    if (caseId) {
      refreshChat(caseId);
    }
  };
  
  window.addEventListener('focus', handleFocus);
  return () => window.removeEventListener('focus', handleFocus);
}, [caseId]);
```

#### Option C: Manual Refresh Button
```javascript
<button onClick={() => refreshChat(caseId)}>
  Refresh Chat
</button>
```

### 8. Message Continuity Guarantees

#### Backend Guarantees
- ✅ All messages are persisted to MongoDB immediately
- ✅ Messages are retrieved in chronological order (sorted by created_at)
- ✅ RAG queries automatically create both user and assistant messages
- ✅ Each message has unique ID for deduplication
- ✅ Timestamps are ISO 8601 format for consistent parsing

#### Frontend Responsibilities
- Display messages in order received
- Handle duplicate messages (use message ID as key)
- Show loading states during API calls
- Scroll to bottom when new messages arrive
- Preserve scroll position when viewing history

### 9. Error Handling

```javascript
async function sendMessageWithRetry(caseId, content, retries = 3) {
  try {
    const response = await fetch(`/api/chat/case/${caseId}/message/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ content, message_type: 'user' })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return await response.json();
    
  } catch (error) {
    if (retries > 0) {
      console.log(`Retrying... (${retries} attempts left)`);
      await new Promise(resolve => setTimeout(resolve, 1000));
      return sendMessageWithRetry(caseId, content, retries - 1);
    }
    
    // Show error to user
    showErrorNotification('Failed to send message. Please try again.');
    throw error;
  }
}
```

### 10. Testing Chat Resumption

#### Test Script
```bash
#!/bin/bash

# 1. Create case and send first message
CASE_ID="your_case_id"
TOKEN="your_jwt_token"

echo "=== Step 1: Get initial chat (should be empty) ==="
curl -X GET "http://localhost:8000/api/chat/case/$CASE_ID/" \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Step 2: Send first message ==="
curl -X POST "http://localhost:8000/api/chat/case/$CASE_ID/message/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is my first message",
    "message_type": "user"
  }'

echo -e "\n\n=== Step 3: Send RAG query ==="
curl -X POST "http://localhost:8000/api/evidence/rag/query/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "'"$CASE_ID"'",
    "query": "What evidence do we have?",
    "top_k": 3
  }'

echo -e "\n\n=== Step 4: Get chat again (should have 3 messages) ==="
curl -X GET "http://localhost:8000/api/chat/case/$CASE_ID/" \
  -H "Authorization: Bearer $TOKEN" | jq '.messages | length'

echo -e "\n\n=== Step 5: Send another message ==="
curl -X POST "http://localhost:8000/api/chat/case/$CASE_ID/message/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Thanks for the information!",
    "message_type": "user"
  }'

echo -e "\n\n=== Step 6: Final chat state (should have 4 messages) ==="
curl -X GET "http://localhost:8000/api/chat/case/$CASE_ID/" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    case_id: .case_id,
    case_name: .case_name,
    total_messages: (.messages | length),
    messages: .messages | map({role, content, timestamp})
  }'
```

## Summary

### Key Points
1. **Single Source of Truth:** GET /api/chat/case/{case_id}/ always returns complete chat history
2. **Auto-Creation:** Chat is automatically created on first message (no manual setup needed)
3. **Dual Methods:** Use /message/ for simple messages, /rag/query/ for evidence searches
4. **Persistent Storage:** All messages saved to MongoDB immediately
5. **Frontend Friendly:** Response format matches UI requirements (role, timestamp, media)

### API Endpoints
```
GET    /api/chat/case/{case_id}/          - Get full chat history
POST   /api/chat/case/{case_id}/message/  - Send regular message
POST   /api/evidence/rag/query/           - Send RAG query (auto-saves to chat)
```

### Workflow
```
Load Case → Check messages.length → Display History → User Types → 
  ├─ Regular Message → POST /message/
  └─ Evidence Query → POST /rag/query/
→ Refresh → Repeat
```

### Future Enhancements
- [ ] WebSocket support for real-time updates
- [ ] Pagination for very long chat histories
- [ ] Message editing/deletion
- [ ] Read receipts
- [ ] Typing indicators
- [ ] Message search/filtering
- [ ] Export chat history
