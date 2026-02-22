# Quick Reference: Chat Resumption

## How to Resume Chat When User Returns to Case

### Backend (Already Implemented ✅)

The chat API automatically handles resumption:

```bash
# Get full chat history for a case
GET /api/chat/case/$CASE_ID/
Authorization: Bearer $TOKEN
```

**Response includes:**
- All previous messages in chronological order
- Case details (id, name, description)
- All evidence files
- Message format: `{id, role, content, timestamp, media}`

### Frontend Implementation

#### 1. Load Case (Initial or Resume)
```javascript
async function loadCase(caseId, token) {
  const response = await fetch(`/api/chat/case/${caseId}/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const data = await response.json();
  
  // Check if resuming or starting new
  if (data.messages.length > 0) {
    console.log(`Resuming chat with ${data.messages.length} messages`);
    displayMessages(data.messages);  // Show all history
    scrollToBottom();
  } else {
    console.log('Starting new conversation');
    showEmptyChat();
  }
  
  return data;
}
```

#### 2. Continue Conversation

**Option A: Regular Message**
```javascript
async function sendMessage(caseId, content, token) {
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
  
  const message = await response.json();
  appendMessage(message);  // Add to UI
}
```

**Option B: RAG Query (Searches Evidence)**
```javascript
async function sendRAGQuery(caseId, query, token) {
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
  
  // RAG automatically creates 2 messages:
  // 1. User's query
  // 2. Assistant's response
  
  // Refresh to show new messages
  loadCase(caseId, token);
}
```

#### 3. Keep Chat Updated

**Polling Strategy:**
```javascript
// Poll every 5 seconds
setInterval(() => {
  refreshChat(caseId, token);
}, 5000);

async function refreshChat(caseId, token) {
  const data = await fetch(`/api/chat/case/${caseId}/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).then(r => r.json());
  
  const currentCount = getCurrentMessageCount();
  
  if (data.messages.length > currentCount) {
    // New messages arrived - add them
    const newMessages = data.messages.slice(currentCount);
    newMessages.forEach(msg => appendMessage(msg));
  }
}
```

### Key Points

1. **Automatic Persistence**: All messages saved to MongoDB immediately
2. **No Manual Setup**: Chat auto-created on first message
3. **Complete History**: GET endpoint always returns full conversation
4. **Two Message Types**:
   - `/message/` - Regular chat messages
   - `/rag/query/` - Evidence search queries (creates user + assistant messages)
5. **Frontend Friendly**: Response uses `role` (user/assistant), `timestamp` (ISO 8601)

### Example Flow

```
User Session 1 (Day 1):
1. Open case → GET /api/chat/case/abc123/ → messages: []
2. Ask question → POST /rag/query/ → 2 messages created
3. Send "Thanks" → POST /message/ → 1 message created
4. Close browser → 3 messages saved

User Session 2 (Day 2):
1. Open same case → GET /api/chat/case/abc123/ → messages: [3 previous messages]
2. Frontend displays all 3 messages
3. User continues conversation → POST /message/ → 4 messages total

User Session 3 (Week Later):
1. Open case → GET /api/chat/case/abc123/ → messages: [all previous messages]
2. Conversation continues seamlessly
```

### Testing

Run the test script:
```bash
cd backend
./test_chat_resumption.sh
```

This script:
1. Loads initial chat state
2. Sends messages
3. Makes RAG queries
4. Reloads chat to verify persistence
5. Shows message counts and timeline

### Troubleshooting

**Q: Messages not persisting?**
- Check MongoDB connection in `.env`
- Verify `case_id` is valid
- Check user owns the case

**Q: Chat shows empty even with messages?**
- Verify GET request includes correct `case_id`
- Check authentication token
- Inspect browser console for errors

**Q: RAG queries don't create messages?**
- Ensure `case_id` is in request body
- Check RAG integration is enabled
- View backend logs for errors

### Complete Documentation

For detailed information:
- [CHAT_RESUMPTION_GUIDE.md](CHAT_RESUMPTION_GUIDE.md) - Complete workflow guide
- [FRONTEND_CHAT_FORMAT.md](FRONTEND_CHAT_FORMAT.md) - API response format
- [RAG_CHAT_INTEGRATION.md](RAG_CHAT_INTEGRATION.md) - RAG integration details

### API Endpoints Summary

```
GET    /api/chat/case/{case_id}/          # Get full chat history (resume)
POST   /api/chat/case/{case_id}/message/  # Send regular message
POST   /api/evidence/rag/query/           # Search evidence (auto-creates messages)
```
