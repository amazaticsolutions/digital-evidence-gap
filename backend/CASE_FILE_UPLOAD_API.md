# Case File Upload API

## Overview

This API endpoint allows users to upload video or image files to a specific case. Files are automatically uploaded to Google Drive and linked to the case in the database.

## Endpoint

```
POST /api/evidence/cases/upload/
```

**Authentication Required:** Yes (JWT Bearer token)

## Features

- ✅ Upload multiple videos/images to a specific case
- ✅ Automatic Google Drive integration
- ✅ Case ownership verification
- ✅ Returns case_id and uploaded file paths
- ✅ Supports batch uploads
- ✅ GPS coordinates and camera metadata
- ✅ Individual file success/failure tracking

## Request

### Headers
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

### Form Data Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | string | **Yes** | ID of the case to upload files to |
| `files` | file(s) | **Yes** | Video or image files (supports multiple) |
| `cam_id` | string | **Yes** | Camera identifier (e.g., "CAM-01") |
| `gps_lat` | float | No | GPS latitude (default: 0.0) |
| `gps_lng` | float | No | GPS longitude (default: 0.0) |
| `folder_id` | string | No | Google Drive folder ID (optional) |

### Supported File Types
- **Videos:** mp4, avi, mov, webm, mkv
- **Images:** jpg, jpeg, png, gif, bmp

## Response

### Success Response (201 Created)

```json
{
  "success": true,
  "case_id": "699a806661a8bbaa3a3e03e6",
  "case_title": "Downtown Theft Investigation",
  "total_files": 3,
  "successful_uploads": 3,
  "failed_uploads": 0,
  "uploaded_files": [
    {
      "evidence_id": "699b123456789abc3a3e03e7",
      "filename": "camera_01_footage.mp4",
      "file_size": 15728640,
      "media_type": "video",
      "gdrive_file_id": "1ABC123XYZ456DEF789",
      "gdrive_url": "https://drive.google.com/file/d/1ABC123XYZ456DEF789/view",
      "cam_id": "CAM-01",
      "gps_lat": 40.7128,
      "gps_lng": -74.0060,
      "uploaded_at": "2026-02-22T10:30:00Z"
    },
    {
      "evidence_id": "699b234567890bcd3a3e03e8",
      "filename": "suspect_screenshot.jpg",
      "file_size": 2048576,
      "media_type": "image",
      "gdrive_file_id": "1GHI789JKL012MNO345",
      "gdrive_url": "https://drive.google.com/file/d/1GHI789JKL012MNO345/view",
      "cam_id": "CAM-01",
      "gps_lat": 40.7128,
      "gps_lng": -74.0060,
      "uploaded_at": "2026-02-22T10:30:02Z"
    }
  ],
  "failed_files": []
}
```

### Error Responses

**400 Bad Request** - Validation error
```json
{
  "error": "Validation failed",
  "details": {
    "case_id": ["This field is required."],
    "files": ["This field is required."]
  }
}
```

**401 Unauthorized** - Not authenticated
```json
{
  "error": "Authentication credentials were not provided."
}
```

**403 Forbidden** - User doesn't own the case
```json
{
  "error": "You don't have permission to upload files to this case"
}
```

**404 Not Found** - Case doesn't exist
```json
{
  "error": "Case not found"
}
```

**500 Internal Server Error** - Upload failed
```json
{
  "error": "Upload failed",
  "details": "Error message details"
}
```

## Usage Examples

### Example 1: Single File Upload

```bash
curl -X POST http://localhost:8000/api/evidence/cases/upload/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "case_id=699a806661a8bbaa3a3e03e6" \
  -F "files=@/path/to/video.mp4" \
  -F "cam_id=CAM-01" \
  -F "gps_lat=40.7128" \
  -F "gps_lng=-74.0060"
```

### Example 2: Multiple Files Upload

```bash
curl -X POST http://localhost:8000/api/evidence/cases/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "case_id=$CASE_ID" \
  -F "files=@/path/to/video1.mp4" \
  -F "files=@/path/to/video2.mp4" \
  -F "files=@/path/to/image.jpg" \
  -F "cam_id=CAM-01" \
  -F "gps_lat=40.7128" \
  -F "gps_lng=-74.0060"
```

### Example 3: With Custom Google Drive Folder

```bash
curl -X POST http://localhost:8000/api/evidence/cases/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "case_id=$CASE_ID" \
  -F "files=@/path/to/evidence.mp4" \
  -F "cam_id=CAM-02" \
  -F "gps_lat=40.7580" \
  -F "gps_lng=-73.9855" \
  -F "folder_id=1ABC123_CustomFolderID"
```

### Example 4: Python Requests

```python
import requests

url = "http://localhost:8000/api/evidence/cases/upload/"
headers = {
    "Authorization": f"Bearer {access_token}"
}

files = [
    ('files', ('video1.mp4', open('/path/to/video1.mp4', 'rb'), 'video/mp4')),
    ('files', ('video2.mp4', open('/path/to/video2.mp4', 'rb'), 'video/mp4')),
]

data = {
    'case_id': '699a806661a8bbaa3a3e03e6',
    'cam_id': 'CAM-01',
    'gps_lat': 40.7128,
    'gps_lng': -74.0060
}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()

print(f"Success: {result['success']}")
print(f"Case ID: {result['case_id']}")
print(f"Uploaded {result['successful_uploads']} files")

for file_info in result['uploaded_files']:
    print(f"  - {file_info['filename']}: {file_info['gdrive_url']}")
```

### Example 5: JavaScript/Fetch

```javascript
const formData = new FormData();
formData.append('case_id', '699a806661a8bbaa3a3e03e6');
formData.append('cam_id', 'CAM-01');
formData.append('gps_lat', 40.7128);
formData.append('gps_lng', -74.0060);

// Add multiple files
const fileInput = document.getElementById('fileInput');
for (let file of fileInput.files) {
  formData.append('files', file);
}

fetch('http://localhost:8000/api/evidence/cases/upload/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Upload successful:', data);
  console.log('Case ID:', data.case_id);
  console.log('Uploaded files:', data.uploaded_files.length);
  
  data.uploaded_files.forEach(file => {
    console.log(`- ${file.filename}: ${file.gdrive_url}`);
  });
})
.catch(error => {
  console.error('Upload failed:', error);
});
```

## Complete Workflow Example

### Step 1: Authenticate
```bash
# Sign in to get access token
curl -X POST http://localhost:8000/api/users/signin/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "investigator@police.gov",
    "password": "SecurePassword123!"
  }'

# Save the token
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Step 2: Get or Create a Case
```bash
# Create new case
curl -X POST http://localhost:8000/api/search/cases/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mall Parking Lot Incident",
    "description": "Investigation of suspicious activity",
    "query_text": "Find person in red jacket"
  }'

# Save the case ID
export CASE_ID="699a806661a8bbaa3a3e03e6"
```

### Step 3: Upload Files to the Case
```bash
# Upload video evidence
curl -X POST http://localhost:8000/api/evidence/cases/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "case_id=$CASE_ID" \
  -F "files=@/evidence/camera_01.mp4" \
  -F "files=@/evidence/camera_02.mp4" \
  -F "files=@/evidence/suspect_image.jpg" \
  -F "cam_id=CAM-01" \
  -F "gps_lat=40.7128" \
  -F "gps_lng=-74.0060"
```

### Step 4: View Uploaded Files
```bash
# Get case details with evidence
curl -X GET http://localhost:8000/api/chat/case/$CASE_ID/ \
  -H "Authorization: Bearer $TOKEN"
```

## Response Fields Explained

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Overall upload success status |
| `case_id` | string | ID of the case files were uploaded to |
| `case_title` | string | Title of the case |
| `total_files` | integer | Total number of files attempted |
| `successful_uploads` | integer | Number of successfully uploaded files |
| `failed_uploads` | integer | Number of failed uploads |
| `uploaded_files` | array | List of successfully uploaded files |
| `failed_files` | array | List of failed uploads with error details |

### Uploaded File Object

| Field | Type | Description |
|-------|------|-------------|
| `evidence_id` | string | Unique evidence ID in database |
| `filename` | string | Original filename |
| `file_size` | integer | File size in bytes |
| `media_type` | string | Type: "video" or "image" |
| `gdrive_file_id` | string | Google Drive file ID |
| `gdrive_url` | string | Direct Google Drive URL |
| `cam_id` | string | Camera identifier |
| `gps_lat` | float | GPS latitude |
| `gps_lng` | float | GPS longitude |
| `uploaded_at` | datetime | Upload timestamp (ISO 8601) |

## Integration with RAG System

After uploading files to a case, you can ingest them into the RAG system for AI-powered analysis:

```bash
# 1. Upload files to case
RESPONSE=$(curl -s -X POST http://localhost:8000/api/evidence/cases/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "case_id=$CASE_ID" \
  -F "files=@video.mp4" \
  -F "cam_id=CAM-01")

# 2. Extract gdrive_file_id from response
GDRIVE_FILE_ID=$(echo $RESPONSE | jq -r '.uploaded_files[0].gdrive_file_id')

# 3. Ingest into RAG system
curl -X POST http://localhost:8000/api/evidence/rag/ingest/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"gdrive_file_id\": \"$GDRIVE_FILE_ID\",
    \"cam_id\": \"CAM-01\",
    \"gps_lat\": 40.7128,
    \"gps_lng\": -74.0060
  }"

# 4. Query the evidence
curl -X POST http://localhost:8000/api/evidence/rag/query/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"case_id\": \"$CASE_ID\",
    \"query\": \"Show me all frames with people\",
    \"top_k\": 10
  }"
```

## Best Practices

1. **File Size Limits:** Maximum file size is 500MB per file (configurable)
2. **Batch Uploads:** Upload multiple files in a single request for efficiency
3. **GPS Coordinates:** Always provide accurate GPS data for location-based analysis
4. **Camera IDs:** Use consistent camera naming conventions (e.g., CAM-01, CAM-02)
5. **Error Handling:** Always check `failed_files` array in response
6. **Case Verification:** Ensure case_id is valid before uploading

## Troubleshooting

### Upload Failed
- Check file format is supported
- Verify file size is under limit
- Ensure Google Drive credentials are configured
- Check case_id is valid and you own the case

### Permission Denied
- Verify JWT token is valid and not expired
- Ensure you own the case you're uploading to
- Check authentication headers are correct

### Files Not Appearing
- Verify successful response with `success: true`
- Check `uploaded_files` array contains your files
- View case details to confirm files are linked

## Related Endpoints

- `POST /api/search/cases/` - Create a new case
- `GET /api/search/cases/` - List all cases
- `GET /api/chat/case/{case_id}/` - Get case details with files
- `POST /api/evidence/rag/ingest/` - Ingest video into RAG
- `POST /api/evidence/rag/query/` - Query evidence with AI

## Notes

- Files are automatically uploaded to Google Drive
- Case ownership is verified before upload
- Failed uploads don't affect successful ones
- Upload timestamps are in UTC
- Each file gets a unique evidence_id
- Google Drive URLs are shareable (with proper permissions)
