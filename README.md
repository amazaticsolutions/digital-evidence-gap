# Digital Evidence Gap

A production-ready full-stack application for managing digital evidence with secure file uploads to Google Drive, AI-powered search capabilities, and a modern React frontend. Built with clean architecture principles and service layer pattern.

## Features

- **User Management**: Custom user authentication with JWT tokens
- **Evidence Upload**: Secure file upload system with Google Drive integration
- **AI-Powered Search**: Semantic search using LLMs and vector embeddings via LangChain
- **Frame Extraction**: Automatic 1-second frame extraction from uploaded videos with AI-generated context
- **Image Context Generation**: Automatic AI context generation for uploaded images stored in VectorDB
- **Case Management**: Organize evidence by case with metadata and conversation history
- **MongoDB Integration**: NoSQL database with optimized indexing
- **Clean Architecture**: Service layer pattern with separation of concerns
- **Production Ready**: Docker containerization, environment-based configuration
- **Security**: JWT authentication, CORS, file validation, logging

## Tech Stack

### Backend
- **Runtime**: Python 3.12.x
- **Framework**: Django 5.x, Django REST Framework
- **Database**: MongoDB Atlas (PyMongo driver)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **File Storage**: Google Drive API (Service Account)
- **AI / LLM**: OpenAI API, LangChain (LLMs + VectorDB)
- **Containerization**: Docker & Docker Compose
- **Architecture**: Clean Architecture, Service Layer Pattern

### Frontend
- **Framework**: React 18, TypeScript
- **Build Tool**: Vite 6
- **Styling**: Tailwind CSS 4, shadcn/ui (Radix UI primitives)
- **UI Components**: MUI (Material UI), Lucide React icons
- **Routing**: React Router 7
- **Forms**: React Hook Form
- **Charts**: Recharts
- **Testing**: Cypress

## Project Structure

```
digital-evidence-gap/
│
├── README.md
├── .gitignore
│
├── backend/                          # Django REST API
│   ├── manage.py                     # Django management script
│   ├── requirements.txt              # Python dependencies
│   ├── .env.example                  # Environment variables template
│   ├── .gitignore
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── pytest.ini
│   │
│   ├── core/                         # Django core configuration
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── wsgi.py
│   │   ├── settings.py               # Environment-aware settings
│   │   ├── urls.py                   # Main URL configuration
│   │   └── middleware.py             # Custom middleware
│   │
│   ├── src/                          # Django applications
│   │   ├── users/                    # User management
│   │   │   ├── models.py, serializers.py, views.py, urls.py
│   │   │   └── services.py, selectors.py, permissions.py
│   │   │
│   │   ├── evidence/                 # Evidence management
│   │   │   ├── models.py, serializers.py, views.py, urls.py
│   │   │   └── services.py, selectors.py, permissions.py
│   │   │
│   │   ├── search/                   # Search functionality
│   │   │   ├── models.py, serializers.py, views.py, urls.py
│   │   │   └── services.py, selectors.py, filters.py
│   │   │
│   │   └── common/                   # Shared utilities
│   │       ├── models.py, mixins.py, permissions.py
│   │       └── pagination.py, exceptions.py, validators.py
│   │
│   ├── utils/                        # Utility modules
│   │   ├── mongo_client.py           # MongoDB connection
│   │   ├── google_drive.py           # Google Drive integration
│   │   ├── jwt_helper.py
│   │   ├── file_utils.py
│   │   └── constants.py
│   │
│   ├── scripts/                      # Management scripts
│   │   ├── create_indexes.py         # MongoDB index creation
│   │   └── seed_data.py              # Data seeding
│   │
│   └── tests/                        # Test suite
│
└── frontend/                         # React TypeScript application
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    ├── postcss.config.mjs
    ├── .env.example
    ├── .gitignore
    │
    └── src/
        ├── main.tsx                  # Application entry point
        │
        ├── app/
        │   ├── App.tsx               # Root component
        │   ├── routes.tsx            # Application routing
        │   │
        │   ├── components/           # Shared components
        │   │   ├── Sidebar.tsx
        │   │   ├── MediaUploadCard.tsx
        │   │   ├── figma/            # Figma-generated components
        │   │   └── ui/               # shadcn/ui component library
        │   │       ├── button.tsx, input.tsx, card.tsx
        │   │       ├── dialog.tsx, form.tsx, table.tsx
        │   │       └── ... (full Radix UI component set)
        │   │
        │   ├── layouts/
        │   │   └── MainLayout.tsx    # Main application layout
        │   │
        │   └── pages/
        │       ├── NewCase.tsx       # Create new case page
        │       ├── PastCases.tsx     # Case listing page
        │       └── ChatWorkspace.tsx # AI chat & evidence workspace
        │
        ├── constants/                # App-wide constants
        │   ├── api.constants.ts
        │   ├── newCase.constants.ts
        │   ├── pastCases.constants.ts
        │   ├── chatWorkspace.constants.ts
        │   └── mediaUploadCard.constants.ts
        │
        ├── services/                 # API service layer
        │   ├── cases.service.ts
        │   └── chatWorkspace.service.ts
        │
        └── styles/                   # Global styles
            ├── index.css
            ├── tailwind.css
            ├── fonts.css
            └── theme.css
```

## Prerequisites

### Backend
- Python 3.12.x
- MongoDB Atlas account (or local MongoDB 6.0+)
- Google Cloud Platform account with Drive API enabled
- Docker & Docker Compose (optional)

### Frontend
- Node.js 18.x or higher
- npm 9.x or higher (or pnpm / yarn)

## Installation

### Backend

#### 1. Navigate to the backend directory

```bash
cd backend
```

#### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Django Configuration
DJANGO_ENV=development
SECRET_KEY=your-secret-key-here
DEBUG=True

# MongoDB Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=digital_evidence_gap
MONGODB_USERNAME=your-username
MONGODB_PASSWORD=your-password

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=1440

# Google Drive Configuration
GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH=path/to/service-account.json
GOOGLE_DRIVE_FOLDER_ID=your-drive-folder-id

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

#### 5. Google Drive Setup

1. Create a Google Cloud Project
2. Enable Google Drive API
3. Create a Service Account and download the key JSON file
4. Share the target Drive folder with the service account email
5. Set `GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH` in your `.env`

#### 6. Initialize the database

```bash
# Create MongoDB indexes
python scripts/create_indexes.py

# Seed initial data (optional)
python scripts/seed_data.py
```

#### 7. Run migrations

```bash
python manage.py migrate
```

#### 8. Start the backend server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

---

### Frontend

#### 1. Navigate to the frontend directory

```bash
cd frontend
```

#### 2. Set Node.js version to 20 using nvm

If you don't have nvm installed, follow the [nvm installation guide](https://github.com/nvm-sh/nvm#installing-and-updating) first.

```bash
# Install Node.js 22 (if not already installed)
nvm install 22

# Switch to Node.js 22
nvm use 22

# Verify the version
node --version  # Should print v22.x.x
```

#### 3. Install dependencies

```bash
npm install
```

#### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

#### 4. Start the development server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

#### 5. Build for production

```bash
npm run build
```

---

### Using Docker (Backend)

```bash
cd backend
docker-compose up --build
```

## API Documentation

### Authentication Endpoints

#### Register User

```http
POST /api/users/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Login

```http
POST /api/users/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "user_id",
    "email": "user@example.com"
  }
}
```

### Evidence Endpoints

#### Upload Evidence

```http
POST /api/evidence/upload/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

Form Data:
- file: [image/video file]
- title: "Evidence Title"
- case_name: "Case Name"
```

**Response:**

```json
{
  "id": "evidence_id",
  "title": "Evidence Title",
  "case_name": "Case Name",
  "file_type": "image/jpeg",
  "drive_file_id": "1abc...xyz",
  "drive_url": "https://drive.google.com/file/d/1abc...xyz/view",
  "uploaded_by": "user_id",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### List Evidence

```http
GET /api/evidence/
Authorization: Bearer <access_token>
```

#### Get Evidence Details

```http
GET /api/evidence/{id}/
Authorization: Bearer <access_token>
```

### Search Endpoints

#### Search Evidence

```http
GET /api/search/?q=evidence&file_type=image
Authorization: Bearer <access_token>
```

**Query Parameters:**

- `q`: Search query (semantic search via VectorDB)
- `file_type`: Filter by file type (`image` / `video`)
- `case_name`: Filter by case name
- `uploaded_by`: Filter by user ID

#### Search History

```http
GET /api/search/history/
Authorization: Bearer <access_token>
```

#### Delete Search History

```http
DELETE /api/search/history/{id}/
Authorization: Bearer <access_token>
```

## Testing

### Backend

```bash
cd backend

# Run all tests
python manage.py test

# Run specific app tests
python manage.py test src.users
python manage.py test src.evidence
python manage.py test src.search

# Coverage report
coverage run --source='src' manage.py test
coverage report
```

### Frontend

```bash
cd frontend

# Open Cypress test runner
npm run cy:open

# Run Cypress tests headlessly
npm run cy:run
```

## Security Features

- JWT token-based authentication
- Password hashing with Django's built-in hasher
- File type and size validation
- CORS configuration
- Request/response logging
- Environment-based secret management
- Service account authentication for Google Drive

## Database Collections (MongoDB)

- **users**: User accounts and authentication data
- **cases**: Case metadata, evidence list, and conversation history
- **evidence**: File metadata, Google Drive references, and AI-generated context
- **search_history**: User search queries and filters

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines for Python
- Follow ESLint / TypeScript strict rules for frontend code
- Write tests for new features
- Update documentation
- Use meaningful commit messages
- Follow the existing code structure

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
