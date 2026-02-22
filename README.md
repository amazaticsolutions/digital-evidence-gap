# Digital Evidence Gap API

A production-ready Django REST Framework application for managing digital evidence with secure file uploads to Google Drive, advanced search capabilities, and case-specific chat functionality. Built with clean architecture principles and service layer pattern.

## ⚡ Quick Start

```bash
# 1. Setup (run once from project root)
./setup.sh

# 2. Configure environment
nano backend/.env  # Add your MongoDB URI and credentials

# 3. Run Django server (choose one method)
# Method A: Manual
cd backend && source venv/bin/activate && python manage.py runserver

# Method B: Using helper script (from project root)
./run-django.sh runserver

# 4. Visit API documentation
# http://localhost:8000/swagger/
```

**Important:** All Python packages are in `backend/venv/`. Always activate it before running Django commands!

See [FILE_STRUCTURE_GUIDE.md](FILE_STRUCTURE_GUIDE.md) for detailed usage.

## 🚀 Features

- **User Management**: Custom user authentication with JWT tokens (access & refresh tokens)
- **Evidence Upload**: Secure file upload system with Google Drive integration (single & batch uploads)
- **Case Management**: Create cases with direct file uploads, manage evidence, assign cases, and track investigations
- **Multimedia RAG Pipeline**: Advanced video processing with frame extraction, captioning, and vector embeddings
- **Advanced Search**: Full-text search with history tracking and case-based organization
- **Chat System**: Case-specific messaging for collaboration and investigation notes
- **MongoDB Integration**: NoSQL database with optimized indexing for fast queries
- **Clean Architecture**: Service layer pattern with separation of concerns
- **Production Ready**: Environment-based configuration, comprehensive error handling
- **Security**: JWT authentication, CORS, file validation, request logging
- **API Documentation**: Interactive Swagger/ReDoc documentation with complete endpoint specs

## 🛠 Tech Stack

- **Backend**: Python 3.11+, Django 5.x, Django REST Framework
- **Database**: MongoDB 6.0+ (PyMongo driver)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **File Storage**: Google Drive API (Service Account)
- **AI/ML**: Hugging Face Transformers, OpenAI CLIP, Sentence Transformers
- **Vector Search**: MongoDB Atlas Vector Search
- **API Documentation**: drf-yasg (Swagger/ReDoc)
- **Architecture**: Clean Architecture, Service Layer Pattern

---

## 🎯 Multimedia RAG System

The application includes an advanced **Retrieval-Augmented Generation (RAG)** pipeline for processing and querying video evidence:

### Features:
- **Frame Extraction**: Automatically extract frames from videos at configurable intervals
- **Image Captioning**: Generate descriptive captions for each frame using AI models
- **Vector Embeddings**: Create semantic embeddings for similarity search
- **Semantic Search**: Query frames using natural language
- **Person Re-identification**: Track and identify persons across multiple frames/videos
- **💬 Chat Integration**: All queries and responses automatically stored in case chat history

### RAG Pipeline Components:

1. **Ingestion** (`multimedia_rag/ingestion/`):
   - `video_processor.py`: Extract frames from videos
   - `caption_generator.py`: Generate captions using BLIP/CLIP models
   - `embedding_generator.py`: Create vector embeddings

2. **Query** (`multimedia_rag/query/`):
   - `query_engine.py`: Process natural language queries
   - `retriever.py`: Perform vector similarity search

3. **Storage** (`multimedia_rag/drive/`):
   - `gdrive_client.py`: Manage Google Drive uploads and downloads

### Example RAG Workflow:

```python
# Ingest a video
POST /api/evidence/rag/ingest/
{
  "video_id": "video_123",
  "gdrive_file_id": "gdrive_file_id"
}

# Query for specific frames (automatically stored in case chat)
POST /api/evidence/rag/query/
{
  "case_id": "699a806661a8bbaa3a3e03e6",
  "query": "Show me all frames with a person wearing red",
  "top_k": 10,
  "enable_reid": false
}

# Response includes chat metadata
{
  "chat_id": "60f1e2d3...",
  "user_message_id": "60f1e2d4...",
  "assistant_message_id": "60f1e2d5...",
  "query": "Show me all frames with a person wearing red",
  "total_found": 12,
  "summary": "Found 12 frames showing individuals in red clothing...",
  "results": [...]
}

# View chat history for the case
GET /api/chat/case/{case_id}/
```

For detailed RAG documentation, see:
- [backend/multimedia_rag/README.md](backend/multimedia_rag/README.md)
- [backend/HOW_TO_USE_MULTIMEDIA_RAG.md](backend/HOW_TO_USE_MULTIMEDIA_RAG.md)
- [backend/RAG_CHAT_INTEGRATION.md](backend/RAG_CHAT_INTEGRATION.md) ⭐ **Chat Integration Guide**
- [backend/CHAT_RESUMPTION_GUIDE.md](backend/CHAT_RESUMPTION_GUIDE.md) 🔄 **Chat Resumption & Continuation**
- [backend/FRONTEND_CHAT_FORMAT.md](backend/FRONTEND_CHAT_FORMAT.md) 🎨 **Frontend Response Format**

---

## 📁 Project Structure

```
digital-evidence-gap/
│
├── setup.sh                      # Setup script for initial environment
├── run-django.sh                 # Helper script to run Django server
├── README.md                     # This file
├── FILE_STRUCTURE_GUIDE.md      # Detailed project structure guide
├── SETUP_INSTRUCTIONS.md        # Setup and deployment instructions
│
├── backend/                      # Django backend application
│   ├── manage.py                # Django management script
│   ├── requirements.txt         # Python dependencies
│   ├── pytest.ini               # Pytest configuration
│   ├── .env                     # Environment variables (not in git)
│   ├── db.sqlite3              # SQLite database (development)
│   │
│   ├── core/                    # Django core configuration
│   │   ├── settings.py          # Django settings (environment-aware)
│   │   ├── urls.py              # Main URL configuration & Swagger
│   │   ├── middleware.py        # Custom middleware
│   │   ├── asgi.py, wsgi.py    # Server configurations
│   │
│   ├── users/                   # User management app
│   │   ├── models.py            # User model (MongoDB-based with Django auth)
│   │   ├── serializers.py       # User serializers (SignUp, SignIn, Profile)
│   │   ├── views.py             # Auth views (SignUpView, SignInView, etc.)
│   │   ├── services.py          # Business logic (user creation, authentication)
│   │   ├── selectors.py         # Data retrieval logic
│   │   ├── permissions.py       # Custom permissions
│   │   └── urls.py              # User endpoints
│   │
│   ├── evidence/                # Evidence management app
│   │   ├── models.py            # Evidence metadata models
│   │   ├── serializers.py       # Evidence serializers
│   │   ├── views.py             # Upload, list, detail views
│   │   ├── rag_views.py         # RAG pipeline endpoints
│   │   ├── services.py          # Upload & processing logic
│   │   ├── selectors.py         # Evidence retrieval
│   │   └── urls.py              # Evidence endpoints
│   │
│   ├── search/                  # Case management app
│   │   ├── models.py            # Case models
│   │   ├── serializers.py       # Case serializers (Create, List, Detail, etc.)
│   │   ├── views.py             # Case CRUD operations
│   │   ├── services.py          # Case business logic
│   │   ├── selectors.py         # Case queries
│   │   ├── filters.py           # Search filters
│   │   └── urls.py              # Case endpoints
│   │
│   ├── chat/                    # Chat/messaging app
│   │   ├── models.py            # Chat & Message models
│   │   ├── serializers.py       # Chat serializers
│   │   ├── views.py             # Chat & message endpoints
│   │   ├── services.py          # Chat business logic
│   │   └── urls.py              # Chat endpoints
│   │
│   ├── common/                  # Shared utilities
│   │   ├── models.py            # Base models
│   │   ├── mixins.py            # Common mixins
│   │   ├── permissions.py       # Shared permissions
│   │   ├── pagination.py        # Custom pagination
│   │   ├── exceptions.py        # Custom exceptions
│   │   └── validators.py        # Shared validators
│   │
│   ├── multimedia_rag/          # RAG Processing Pipeline
│   │   ├── main.py              # Main RAG orchestrator
│   │   ├── config.py            # RAG configuration
│   │   ├── ingestion/           # Video ingestion & processing
│   │   │   ├── video_processor.py    # Frame extraction
│   │   │   ├── caption_generator.py  # Image captioning
│   │   │   └── embedding_generator.py # Vector embeddings
│   │   ├── query/               # Query processing
│   │   │   ├── query_engine.py  # Query handler
│   │   │   └── retriever.py     # Vector search
│   │   └── drive/               # Google Drive integration
│   │       └── gdrive_client.py # Drive API client
│   │
│   ├── utils/                   # Utility modules
│   │   ├── mongo_client.py      # MongoDB connection
│   │   ├── google_drive.py      # Google Drive utilities
│   │   └── constants.py         # App constants
│   │
│   ├── scripts/                 # Management scripts
│   │   ├── create_indexes.py    # MongoDB index creation
│   │   └── seed_data.py         # Data seeding
│   │
│   ├── tests/                   # Test suite
│   │   ├── conftest.py          # Pytest fixtures
│   │   ├── test_*.py            # Test files
│   │
│   ├── logs/                    # Application logs
│   ├── uploads/                 # Local file storage
│   └── venv/                    # Python virtual environment
│
└── frontend/                    # Frontend application (if applicable)
    ├── src/
    └── package.json
```

## 📋 Prerequisites

- Python 3.11.x
- MongoDB 6.0+
- Google Cloud Platform account with Drive API enabled
- Docker & Docker Compose (optional)

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd digital-evidence-gap
```

### 2. Run Setup Script (Recommended)

The easiest way to set up the project is using the provided setup script:

```bash
./setup.sh
```

This script will:
- Check for Python 3.11+ installation
- Create a virtual environment in `backend/venv/`
- Install all required dependencies from `backend/requirements.txt`
- Create environment configuration files

### 3. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

Configure your environment variables in `backend/.env`:

```bash
cd backend
cp .env.example .env  # If .env.example exists
nano .env  # Or use your preferred editor
```

Required environment variables:

```env
# Django Configuration
DJANGO_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=digital_evidence_gap
# OR for authenticated MongoDB:
# MONGODB_URI=mongodb://username:password@localhost:27017/digital_evidence_gap

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_LIFETIME=1440  # in minutes (default: 24 hours)
JWT_REFRESH_TOKEN_LIFETIME=43200  # in minutes (default: 30 days)

# Google Drive Configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
GOOGLE_DRIVE_FOLDER_ID=your-google-drive-folder-id

# CORS Configuration (for frontend)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 5. MongoDB Setup

#### Option A: Using Docker
```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:6.0
```

#### Option B: Local Installation
```bash
# Ubuntu/Debian
sudo apt-get install mongodb

# macOS
brew install mongodb-community@6.0

# Start MongoDB service
# Ubuntu/Debian
sudo systemctl start mongodb

# macOS
brew services start mongodb-community@6.0
```

### 6. Google Drive Setup

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google Drive API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

3. **Create Service Account**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the details and create
   - Download the JSON key file

4. **Share Drive Folder**:
   - Create or select a folder in Google Drive
   - Right-click > Share
   - Add the service account email (from JSON key file)
   - Give "Editor" permissions
   - Copy the folder ID from the URL

5. **Configure Environment**:
   - Save the JSON key file to a secure location
   - Update `GOOGLE_APPLICATION_CREDENTIALS` in `.env`
   - Update `GOOGLE_DRIVE_FOLDER_ID` in `.env`

### 7. Create MongoDB Indexes

```bash
cd backend
source venv/bin/activate
python scripts/create_indexes.py
```

### 8. Run Database Migrations

```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

### 9. Create Superuser (Optional)

```bash
cd backend
source venv/bin/activate
python manage.py createsuperuser
```

## 🚀 Running the Application

### Development Mode (Recommended)

#### Method 1: Using Helper Script (from project root)
```bash
./run-django.sh
```

#### Method 2: Manual (from backend directory)
```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

The API will be available at:
- **API Base**: http://localhost:8000/api
- **Swagger Docs**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

### Production Mode

```bash
cd backend
source venv/bin/activate
export DJANGO_ENV=production
python manage.py runserver 0.0.0.0:8000 --noreload
```

### Using Docker (If Configured)

```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up --build

# Run in detached mode
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Additional Management Commands

```bash
cd backend
source venv/bin/activate

# Create MongoDB indexes
python scripts/create_indexes.py

# Seed test data
python scripts/seed_data.py

# Run Django shell
python manage.py shell

# Check for errors
python manage.py check

# Collect static files (for production)
python manage.py collectstatic

# Create superuser
python manage.py createsuperuser
```

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api
```

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

---

### Authentication Endpoints

#### Sign Up (Register User)
```bash
POST /api/users/signup/
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "phone_number": "+1234567890",
  "organization": "Your Organization"
}
```

**Response (201 Created):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "699a7f3761a8bbaa3a3e03e4",
    "email": "user@example.com",
    "phone_number": "+1234567890",
    "organization": "Your Organization",
    "role": "analyst",
    "created_at": "2026-02-22T03:59:51.987719Z",
    "updated_at": "2026-02-22T03:59:51.987719Z"
  }
}
```

#### Sign In (Login)
```bash
POST /api/users/signin/
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "699a7f3761a8bbaa3a3e03e4",
    "email": "user@example.com",
    "phone_number": "+1234567890",
    "organization": "Your Organization",
    "role": "analyst",
    "created_at": "2026-02-22T03:59:51.987000Z",
    "updated_at": "2026-02-22T03:59:51.987000Z"
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/users/signin/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### Refresh Access Token
```bash
POST /api/users/refresh/
Content-Type: application/json
```

**Request Body:**
```json
{
  "refresh": "your_refresh_token_here"
}
```

**Response (200 OK):**
```json
{
  "access": "new_access_token_here"
}
```

#### Get User Profile
```bash
GET /api/users/me/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "699a7f3761a8bbaa3a3e03e4",
  "email": "user@example.com",
  "phone_number": "+1234567890",
  "organization": "Your Organization",
  "role": "analyst",
  "created_at": "2026-02-22T03:59:51.987000Z",
  "updated_at": "2026-02-22T03:59:51.987000Z"
}
```

#### Update User Profile
```bash
PATCH /api/users/me/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "phone_number": "+9876543210",
  "organization": "New Organization"
}
```

---

### Case Management Endpoints

#### Create Case (with Optional File Uploads)
```bash
POST /api/search/cases/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Data:**
- `title` (required): Case title
- `description` (optional): Case description
- `evidence_files` (optional): Multiple evidence files to upload
- `cam_id` (optional): Camera identifier
- `gps_lat` (optional): GPS latitude
- `gps_lng` (optional): GPS longitude

**Response (201 Created):**
```json
{
  "id": "699a806661a8bbaa3a3e03e6",
  "case_id": "CASE-851221DA",
  "title": "Investigation Case - Missing Evidence 2026",
  "description": "Case involving analysis of surveillance footage...",
  "user_id": "699a7f3761a8bbaa3a3e03e4",
  "assigned_to_user_id": null,
  "assigned_at": null,
  "evidence_count": 0,
  "evidence_ids": [],
  "status": "active",
  "created_at": "2026-02-22T04:04:54.702158Z",
  "updated_at": "2026-02-22T04:04:54.702158Z"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/search/cases/ \
  -H "Authorization: Bearer <access_token>" \
  -F "title=Investigation Case - Missing Evidence 2026" \
  -F "description=Case involving analysis of surveillance footage"
```

#### List All Cases (Detailed)
```bash
GET /api/search/cases/
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `status` (optional): Filter by status (`active`, `completed`, `archived`, `pending`)
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Maximum results (default: 50)

**Response (200 OK):**
```json
{
  "cases": [
    {
      "id": "699a806661a8bbaa3a3e03e6",
      "case_id": "CASE-851221DA",
      "title": "Investigation Case - Missing Evidence 2026",
      "description": "Case involving analysis...",
      "user_id": "699a7f3761a8bbaa3a3e03e4",
      "assigned_to_user_id": null,
      "assigned_at": null,
      "evidence_count": 0,
      "evidence_ids": [],
      "status": "active",
      "created_at": "2026-02-22T04:04:54.702000Z",
      "updated_at": "2026-02-22T04:04:54.702000Z"
    }
  ],
  "total": 1
}
```

**cURL Example:**
```bash
# Get all cases
curl -X GET http://localhost:8000/api/search/cases/ \
  -H "Authorization: Bearer <access_token>"

# Filter by status
curl -X GET "http://localhost:8000/api/search/cases/?status=active&limit=10" \
  -H "Authorization: Bearer <access_token>"
```

#### Get Case Summary (Simplified List)
```bash
GET /api/search/cases/summary/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "cases": [
    {
      "id": "699a806661a8bbaa3a3e03e6",
      "title": "Investigation Case - Missing Evidence 2026",
      "evidence_count": 0,
      "created_at": "2026-02-22T04:04:54.702000Z"
    }
  ],
  "total": 1
}
```

#### Get Specific Case Details
```bash
GET /api/search/cases/{case_id}/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "699a806661a8bbaa3a3e03e6",
  "case_id": "CASE-851221DA",
  "title": "Investigation Case - Missing Evidence 2026",
  "description": "Case involving analysis...",
  "user_id": "699a7f3761a8bbaa3a3e03e4",
  "assigned_to_user_id": null,
  "assigned_at": null,
  "evidence_count": 0,
  "evidence_ids": [],
  "status": "active",
  "created_at": "2026-02-22T04:04:54.702000Z",
  "updated_at": "2026-02-22T04:04:54.702000Z",
  "evidence": []
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/search/cases/699a806661a8bbaa3a3e03e6/ \
  -H "Authorization: Bearer <access_token>"
```

#### Update Case
```bash
PATCH /api/search/cases/{case_id}/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Data:**
- `title` (optional): Updated case title
- `description` (optional): Updated description
- `status` (optional): Updated status

#### Delete Case
```bash
DELETE /api/search/cases/{case_id}/
Authorization: Bearer <access_token>
```

**Response (204 No Content)**

#### Add Evidence to Case
```bash
POST /api/search/cases/{case_id}/evidence/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "evidence_id": "evidence_id_here"
}
```

#### Remove Evidence from Case
```bash
DELETE /api/search/cases/{case_id}/evidence/{evidence_id}/
Authorization: Bearer <access_token>
```

#### Assign Case to User
```bash
POST /api/search/cases/{case_id}/assign/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "user_id_here"
}
```

---

### Evidence Management Endpoints

#### Upload Evidence (Local Storage)
```bash
POST /api/evidence/upload/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Data:**
- `video` (required): Video file
- `cam_id` (required): Camera identifier
- `gps_lat` (optional): GPS latitude
- `gps_lng` (optional): GPS longitude
- `case_id` (optional): Associated case ID

#### Upload Evidence to Google Drive (Single or Multiple Files)
```bash
POST /api/evidence/gdrive/upload/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Data:**
- `files` (required): One or more files to upload
- `cam_id` (required): Camera identifier
- `gps_lat` (optional): GPS latitude
- `gps_lng` (optional): GPS longitude
- `case_id` (optional): Associated case ID
- `folder_id` (optional): Target Google Drive folder ID

**Response (201 Created):**
```json
{
  "batch_id": "BATCH-A1B2C3D4E5F6",
  "total_files": 3,
  "successful_uploads": 3,
  "failed_uploads": 0,
  "evidence_ids": ["id1", "id2", "id3"],
  "results": [
    {
      "success": true,
      "filename": "video1.mp4",
      "evidence_id": "evidence_id_1",
      "gdrive_file_id": "gdrive_file_id_1",
      "gdrive_url": "https://drive.google.com/file/d/..."
    }
  ]
}
```

#### Upload Files to Specific Case
```bash
POST /api/evidence/cases/upload/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Data:**
- `case_id` (required): ID of the case to upload files to
- `files` (required): One or more video/image files
- `cam_id` (required): Camera identifier
- `gps_lat` (optional): GPS latitude (default: 0.0)
- `gps_lng` (optional): GPS longitude (default: 0.0)
- `folder_id` (optional): Google Drive folder ID

**Response (201 Created):**
```json
{
  "success": true,
  "case_id": "699a806661a8bbaa3a3e03e6",
  "case_title": "Downtown Theft Investigation",
  "total_files": 2,
  "successful_uploads": 2,
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
    }
  ],
  "failed_files": []
}
```

**Features:**
- ✅ Automatic case ownership verification
- ✅ Returns case_id and complete file paths
- ✅ Supports multiple file upload
- ✅ Auto-links files to case
- ✅ Google Drive integration

**Example:**
```bash
# Upload videos to case
curl -X POST http://localhost:8000/api/evidence/cases/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "case_id=699a806661a8bbaa3a3e03e6" \
  -F "files=@/path/to/video1.mp4" \
  -F "files=@/path/to/video2.mp4" \
  -F "cam_id=CAM-01" \
  -F "gps_lat=40.7128" \
  -F "gps_lng=-74.0060"
```
      "gdrive_url": "https://drive.google.com/file/d/..."
    }
  ]
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/evidence/gdrive/upload/ \
  -H "Authorization: Bearer <access_token>" \
  -F "files=@video1.mp4" \
  -F "files=@video2.mp4" \
  -F "cam_id=CAM001" \
  -F "case_id=699a806661a8bbaa3a3e03e6"
```

#### Register Google Drive Link
```bash
POST /api/evidence/gdrive/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "gdrive_url": "https://drive.google.com/file/d/FILE_ID/view",
  "cam_id": "CAM001",
  "gps_lat": 12.345,
  "gps_lng": 67.890,
  "case_id": "699a806661a8bbaa3a3e03e6"
}
```

#### Batch Register Google Drive Files
```bash
POST /api/evidence/gdrive/batch/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "files": [
    {
      "gdrive_file_id": "FILE_ID_1",
      "filename": "video1.mp4"
    },
    {
      "gdrive_file_id": "FILE_ID_2",
      "filename": "video2.mp4"
    }
  ],
  "cam_id": "CAM001",
  "gps_lat": 12.345,
  "gps_lng": 67.890,
  "case_id": "699a806661a8bbaa3a3e03e6"
}
```

#### List Evidence/Videos
```bash
GET /api/evidence/videos/
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `case_id` (optional): Filter by case
- `status` (optional): Filter by processing status
- `limit` (optional): Maximum results
- `skip` (optional): Pagination offset

#### Get Evidence Details
```bash
GET /api/evidence/videos/{video_id}/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "video_id",
  "filename": "video1.mp4",
  "file_path": "https://drive.google.com/file/d/...",
  "gdrive_file_id": "gdrive_file_id",
  "cam_id": "CAM001",
  "gps_lat": 12.345,
  "gps_lng": 67.890,
  "case_id": "699a806661a8bbaa3a3e03e6",
  "media_type": "video",
  "file_size": 52428800,
  "status": "uploaded",
  "upload_date": "2026-02-22T04:04:54.702000Z",
  "uploaded_by": "699a7f3761a8bbaa3a3e03e4"
}
```

#### Delete Evidence
```bash
DELETE /api/evidence/videos/{video_id}/
Authorization: Bearer <access_token>
```

**Response (204 No Content)**

#### Start RAG Processing
```bash
POST /api/evidence/process/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "video_id": "video_id_here"
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "job_id_here",
  "status": "processing",
  "video_id": "video_id_here"
}
```

#### Get Processing Job Status
```bash
GET /api/evidence/jobs/{job_id}/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "job_id": "job_id_here",
  "video_id": "video_id_here",
  "status": "completed",
  "progress": 100,
  "created_at": "2026-02-22T04:04:54.702000Z",
  "updated_at": "2026-02-22T04:10:23.158000Z"
}
```

---

### Multimedia RAG Endpoints

#### Ingest Video into RAG System
```bash
POST /api/evidence/rag/ingest/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "video_id": "video_id_here",
  "gdrive_file_id": "gdrive_file_id_here",
  "options": {
    "extract_frames": true,
    "generate_captions": true,
    "create_embeddings": true
  }
}
```

#### Query RAG System for Frames
```bash
POST /api/evidence/rag/query/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "case_id": "699a806661a8bbaa3a3e03e6",
  "query": "Find all frames showing a person wearing a red jacket",
  "top_k": 10,
  "enable_reid": false,
  "filters": {
    "video_id": "video_id_here",
    "cam_id": "CAM-01"
  }
}
```

**Response (200 OK):**
```json
{
  "chat_id": "60f1e2d3c4b5a6e7f8g9h0i1",
  "user_message_id": "60f1e2d3c4b5a6e7f8g9h0i2",
  "assistant_message_id": "60f1e2d3c4b5a6e7f8g9h0i3",
  "query": "Find all frames showing a person wearing a red jacket",
  "total_searched": 4500,
  "total_found": 12,
  "summary": "Found 12 frames showing individuals wearing red jackets across 3 cameras...",
  "results": [
    {
      "id": "frame_001",
      "video_id": "video_id_here",
      "cam_id": "CAM-01",
      "timestamp": 12.5,
      "score": 95.5,
      "relevant": true,
      "explanation": "Person wearing red jacket clearly visible in center frame",
      "caption": "A person wearing a red jacket walking",
      "gps_lat": 40.7128,
      "gps_lng": -74.0060,
      "gdrive_url": "https://drive.google.com/file/d/...",
      "confidence": 0.92
    }
  ],
  "timeline": [...],
  "search_method": "hybrid",
  "queries_used": ["person wearing red jacket", "individual in red clothing"]
}
```

**Note:** Queries and responses are automatically saved to the case chat history. View chat history via `GET /api/chat/case/{case_id}/`

#### Get RAG System Statistics
```bash
GET /api/evidence/rag/stats/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "total_videos": 15,
  "total_frames": 4500,
  "total_embeddings": 4500,
  "index_size_mb": 125.5,
  "last_updated": "2026-02-22T04:10:23.158000Z"
}
```

---

### Chat System Endpoints

#### Get Complete Case Details (with Chat & Evidence)
```bash
GET /api/chat/case/{case_id}/
Authorization: Bearer <access_token>
```

**Response (200 OK) - Frontend Compatible Format:**
```json
{
  "case_id": "699a806661a8bbaa3a3e03e6",
  "case_name": "State v. Anderson - Robbery Investigation",
  "case_description": "A high-profile case involving allegations of armed robbery and digital evidence tampering.",
  "total_evidence_files": 3,
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
      "role": "user",
      "content": "What happened between 3:15 PM and 3:30 PM on February 14th?",
      "timestamp": "2026-02-22T14:35:00Z",
      "media": []
    },
    {
      "id": "60f1e2d3c4b5a6e7f8g9h0i2",
      "role": "assistant",
      "content": "Based on the evidence, at 3:18 PM, a black sedan was observed entering the parking lot from the north entrance. At 3:22 PM, two individuals exited the vehicle and approached the building entrance. The security camera footage shows clear visibility of both subjects.",
      "timestamp": "2026-02-22T14:35:05Z",
      "media": []
    },
    {
      "id": "60f1e2d3c4b5a6e7f8g9h0i3",
      "role": "user",
      "content": "What are the potential legal implications of the evidence presented?",
      "timestamp": "2026-02-22T14:40:00Z",
      "media": []
    },
    {
      "id": "60f1e2d3c4b5a6e7f8g9h0i4",
      "role": "assistant",
      "content": "The evidence presented could lead to several legal implications, including charges of armed robbery, data theft, and possibly conspiracy if others are found to be involved. The strength of the digital evidence, such as the camera footage and witness testimony, will play a crucial role in determining the outcome of the case.",
      "timestamp": "2026-02-22T14:40:08Z",
      "media": []
    }
  ]
}
```

**Response Fields:**
- `case_id` (string): Unique case identifier
- `case_name` (string): Case title/name
- `case_description` (string): Case description
- `total_evidence_files` (integer): Total number of evidence files
- `evidence_files` (array): All evidence files for the case
  - `type` (string): Media type - "video" or "image"
  - `url` (string): Google Drive URL or file path
  - `description` (string): File description
  - `filename` (string): Original filename
  - `file_size` (integer): File size in bytes
  - `upload_date` (string): Upload timestamp (ISO 8601)
- `messages` (array): Chat conversation history
  - `id` (string): Message ID
  - `role` (string): Message role - "user" or "assistant"
  - `content` (string): Message content
  - `timestamp` (string): Message timestamp (ISO 8601)
  - `media` (array): Media items attached to this message

**Note:** RAG queries are automatically saved to chat history with role="assistant"

**📖 Chat Resumption:**
Users can resume conversations when returning to a case. The API automatically persists all messages and retrieves complete chat history. See [CHAT_RESUMPTION_GUIDE.md](backend/CHAT_RESUMPTION_GUIDE.md) for detailed workflow, frontend integration examples, and testing scripts.

#### Send Message to Case Chat
```bash
POST /api/chat/case/{case_id}/message/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "Can you analyze the footage from camera 2?",
  "message_type": "user"
}
```

**Request Fields:**
- `content` (string, required): Message content
- `message_type` (string, optional): Message type - "user", "assistant", or "system" (default: "user")

**Response (201 Created):**
```json
{
  "id": "60f1e2d3c4b5a6e7f8g9h0i5",
  "chat_id": "60f1e2d3c4b5a6e7f8g9h0i1",
  "user_id": 123,
  "content": "Can you analyze the footage from camera 2?",
  "message_type": "user",
  "created_at": "2026-02-22T15:00:00Z"
}
```

**Message Roles:**
- `user`: Messages from investigators/users
- `assistant`: Automated responses from RAG/AI system
- `system`: System notifications and updates

**Example Usage:**
```bash
# Send user message
curl -X POST http://localhost:8000/api/chat/case/699a806661a8bbaa3a3e03e6/message/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What happened at 3:15 PM?",
    "message_type": "user"
  }'

# Get chat history
curl -X GET http://localhost:8000/api/chat/case/699a806661a8bbaa3a3e03e6/ \
  -H "Authorization: Bearer $TOKEN"
```
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/chat/case/699a806661a8bbaa3a3e03e6/ \
  -H "Authorization: Bearer <access_token>"
```

#### Send Message to Case Chat
```bash
POST /api/chat/case/{case_id}/message/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "Can you identify the person in frame 125?",
  "message_type": "user"
}
```

**Response (201 Created):**
```json
{
  "id": "msg_id",
  "chat_id": "chat_id",
  "user_id": "699a7f3761a8bbaa3a3e03e4",
  "content": "Can you identify the person in frame 125?",
  "message_type": "user",
  "created_at": "2026-02-22T04:45:23.158000Z"
}
```

**Message Types:**
- `user`: Message from user
- `assistant`: Response from AI/system
- `system`: System notifications

---

### API Documentation Endpoints

#### Swagger UI (Interactive)
```bash
GET /swagger/
```
Provides interactive API documentation where you can test endpoints directly from the browser.

#### ReDoc (Documentation)
```bash
GET /redoc/
```
Provides clean, readable API documentation.

#### OpenAPI Schema (JSON)
```bash
GET /swagger.json
```

#### OpenAPI Schema (YAML)
```bash
GET /swagger.yaml
```

---

## 🧪 Testing

### Run All Tests

```bash
cd backend
source venv/bin/activate
pytest
```

### Run Specific Test Files

```bash
# Test a specific module
pytest tests/test_users.py

# Test specific apps
pytest users/tests.py
pytest evidence/tests.py
pytest search/tests.py
pytest chat/tests.py
```

### Run Tests with Coverage

```bash
# Generate coverage report
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Django Tests (Alternative)

```bash
# Run all Django tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test evidence
python manage.py test search
python manage.py test chat
```

### Test Authentication APIs

Use the provided test script:

```bash
cd backend
python test_auth_apis.py
```

This script will:
- Create a new test user via Sign Up API
- Authenticate the user via Sign In API
- Display access and refresh tokens
- Show full request/response details

### Manual API Testing with cURL

```bash
# Example: Test Sign Up
curl -X POST http://localhost:8000/api/users/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!"
  }'

# Example: Test Sign In
curl -X POST http://localhost:8000/api/users/signin/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# Example: Create Case
curl -X POST http://localhost:8000/api/search/cases/ \
  -H "Authorization: Bearer <your_access_token>" \
  -F "title=Test Case" \
  -F "description=Test Description"
```

---

## 🔒 Security Features

- JWT token-based authentication
- Password hashing with Django's built-in hasher
- File type and size validation
- CORS configuration
- Request/response logging
- Environment-based secret management
- Service account authentication for Google Drive

## 🐳 Docker Deployment

### Build and Run

```bash
# Development
docker-compose -f docker/docker-compose.yml up --build

# Production
docker-compose -f docker/docker-compose.prod.yml up --build -d
```

### Docker Commands

```bash
# View logs
docker-compose logs -f

# Run commands in container
docker-compose exec web python manage.py shell

# Stop services
docker-compose down
```

## 📊 Database Management

### MongoDB Collections

The application uses MongoDB for storing:

- **users**: User accounts (integrated with Django authentication)
  - Fields: email, password (hashed), phone_number, organization, role
  - Indexes: email (unique)

- **cases**: Investigation cases
  - Fields: case_id, title, description, user_id, status, evidence_ids
  - Indexes: user_id, status, created_at

- **evidence**: File metadata and Google Drive references
  - Fields: filename, gdrive_file_id, cam_id, gps_lat, gps_lng, case_id
  - Indexes: uploaded_by, case_id, status

- **chats**: Case-specific chat conversations
  - Fields: case_id, user_id, title
  - Indexes: case_id (unique), user_id

- **messages**: Chat messages
  - Fields: chat_id, user_id, content, message_type
  - Indexes: chat_id, user_id

- **search_history**: User search queries
  - Fields: user_id, query, filters, results_count
  - Indexes: user_id, created_at

- **frames**: Extracted video frames (RAG pipeline)
  - Fields: video_id, frame_number, timestamp, caption, embedding
  - Indexes: video_id, vector index on embeddings

### Index Management

Create or recreate MongoDB indexes:

```bash
cd backend
source venv/bin/activate
python scripts/create_indexes.py
```

### Indexes Created:
- `users.email` - Unique index
- `cases.user_id` - Regular index
- `evidence.uploaded_by` - Regular index
- `evidence.case_id` - Regular index
- `chats.case_id` - Unique index
- `messages.chat_id` - Regular index
- `frames.embeddings` - Vector index for similarity search

### Database Utilities

```bash
# Check MongoDB connection
cd backend
source venv/bin/activate
python check_mongo_data.py

# Verify embeddings
python check_embeddings.py

# Check index status
python check_index_status.py
```

---

## 🔧 Development

### Project Architecture

The application follows **Clean Architecture** principles with a **Service Layer Pattern**:

- **Views** (`views.py`): Handle HTTP requests/responses and validation
- **Serializers** (`serializers.py`): Data validation and serialization
- **Services** (`services.py`): Business logic and operations
- **Selectors** (`selectors.py`): Data retrieval and queries
- **Models** (`models.py`): Data schemas and MongoDB document definitions
- **Permissions** (`permissions.py`): Access control logic

### Code Organization

```
Each Django app follows this structure:
app_name/
├── models.py        # MongoDB document schemas
├── serializers.py   # Request/response serializers
├── views.py         # API endpoints (ViewSets/APIViews)
├── services.py      # Business logic (create, update, delete)
├── selectors.py     # Data retrieval (get, list, filter)
├── permissions.py   # Custom permissions
├── urls.py          # URL routing
└── tests.py         # Unit tests
```

### Code Style & Formatting

```bash
cd backend
source venv/bin/activate

# Format code with Black
black .

# Sort imports with isort
isort .

# Lint code with flake8
flake8 .

# Type checking with mypy (if configured)
mypy .
```

### Pre-commit Hooks (Optional)

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### Environment Variables

Development vs Production configurations:

```bash
# Development (.env)
DJANGO_ENV=development
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Production (.env)
DJANGO_ENV=production
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Debugging

```bash
# Enable Django debug toolbar (if installed)
DEBUG=True

# View logs
tail -f backend/logs/django.log

# Python debugger
import pdb; pdb.set_trace()  # Add this line in your code
```

---

## 📈 Roadmap

### ✅ Completed Features
- [x] User authentication with JWT (access & refresh tokens)
- [x] Sign Up, Sign In, and Profile management APIs
- [x] Evidence upload (single and batch) to Google Drive
- [x] Local and Google Drive file storage integration
- [x] Case management with CRUD operations
- [x] Assign cases to users
- [x] Link evidence to cases
- [x] Chat system for case discussions
- [x] Full-text search and filtering
- [x] Query parameters for pagination and filtering
- [x] API documentation with Swagger/ReDoc
- [x] MongoDB integration with optimized indexes
- [x] Google Drive API integration with service accounts
- [x] Multimedia RAG processing pipeline
  - [x] Frame extraction from videos
  - [x] Image captioning with AI models
  - [x] Vector embeddings generation
  - [x] Vector similarity search
- [x] Person re-identification capabilities
- [x] Service layer architecture pattern
- [x] Comprehensive error handling and logging

### 🔄 In Progress
- [ ] Enhanced RAG query capabilities
- [ ] Real-time processing status updates
- [ ] WebSocket support for chat
- [ ] Admin dashboard improvements
- [ ] Batch processing optimization

### 🚀 Planned Enhancements
- [ ] **Performance**:
  - [ ] API rate limiting and throttling
  - [ ] Redis caching layer
  - [ ] Database query optimization
  - [ ] Response compression

- [ ] **Features**:
  - [ ] Advanced analytics and reporting
  - [ ] Export evidence and case reports (PDF)
  - [ ] Timeline visualization for cases
  - [ ] Audit logging and compliance features
  - [ ] Multi-language support

- [ ] **Integration**:
  - [ ] Integration with external forensic tools
  - [ ] Webhook notifications
  - [ ] Email notifications for case updates
  - [ ] Third-party authentication (OAuth2)

- [ ] **Scalability**:
  - [ ] Background task processing with Celery
  - [ ] Message queue (RabbitMQ/Redis)
  - [ ] Horizontal scaling support
  - [ ] Load balancing configuration

- [ ] **DevOps**:
  - [ ] CI/CD pipeline setup
  - [ ] Automated testing in pipeline
  - [ ] Docker production optimization
  - [ ] Kubernetes deployment configs

- [ ] **Mobile**:
  - [ ] Mobile API optimization
  - [ ] Mobile app companion
  - [ ] Push notifications

---

## 📖 Additional Documentation

For more detailed documentation, see:

- [FILE_STRUCTURE_GUIDE.md](FILE_STRUCTURE_GUIDE.md) - Complete project structure guide
- [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) - Detailed setup and deployment guide
- [backend/TESTING_GUIDE.md](backend/TESTING_GUIDE.md) - Testing documentation
- [backend/multimedia_rag/README.md](backend/multimedia_rag/README.md) - RAG pipeline documentation
- [backend/multimedia_rag/QUICKSTART.md](backend/multimedia_rag/QUICKSTART.md) - RAG quick start guide
- [backend/MULTIMEDIA_RAG_API.md](backend/MULTIMEDIA_RAG_API.md) - RAG API documentation

---

## 🆘 Troubleshooting

### Common Issues

**MongoDB Connection Error:**
```bash
# Check if MongoDB is running
sudo systemctl status mongodb  # Linux
brew services list | grep mongo  # macOS

# Check connection string in .env
MONGODB_URI=mongodb://localhost:27017/
```

**Google Drive Upload Fails:**
```bash
# Verify service account credentials
ls -la /path/to/service-account-key.json

# Check folder permissions in Google Drive
# Ensure service account email has Editor access
```

**Module Import Errors:**
```bash
# Ensure virtual environment is activated
source backend/venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

**Port Already in Use:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or run on different port
python manage.py runserver 8001
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Follow existing code style
   - Write tests for new features
   - Update documentation
4. **Test your changes**
   ```bash
   pytest
   ```
5. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Coding Guidelines

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Write docstrings for functions and classes
- Keep functions small and focused
- Use type hints where appropriate
- Write tests for new features
- Update documentation for API changes

### Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example:**
```
feat(evidence): add batch upload support

Implemented batch upload functionality for Google Drive
that allows multiple files to be uploaded in a single request.

Closes #123
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

For support and questions:

- **Email**: support@digital-evidence-gap.com
- **Issues**: Create an issue in the repository
- **Documentation**: Check the docs folder for guides

---

## 🙏 Acknowledgments

- Django REST Framework for the excellent API framework
- MongoDB for flexible NoSQL database
- Google Drive API for file storage integration
- OpenAI/Hugging Face for AI/ML capabilities
- All contributors and supporters

---

**Built with ❤️ for Digital Forensics and Evidence Management**

