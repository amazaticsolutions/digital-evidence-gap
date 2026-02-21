# Digital Evidence Gap API

A production-ready Django REST Framework application for managing digital evidence with secure file uploads to Google Drive and advanced search capabilities. Built with clean architecture principles and service layer pattern.

## 🚀 Features

- **User Management**: Custom user authentication with JWT tokens
- **Evidence Upload**: Secure file upload system with Google Drive integration
- **Advanced Search**: Full-text search with history tracking
- **MongoDB Integration**: NoSQL database with optimized indexing
- **Clean Architecture**: Service layer pattern with separation of concerns
- **Production Ready**: Docker containerization, environment-based configuration
- **Security**: JWT authentication, CORS, file validation, logging
- **API Documentation**: RESTful endpoints with proper error handling

## 🛠 Tech Stack

- **Backend**: Python 3.12.x, Django 5.x.x, Django REST Framework
- **Database**: MongoDB (PyMongo driver)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **File Storage**: Google Drive API (Service Account)
- **Containerization**: Docker & Docker Compose
- **Architecture**: Clean Architecture, Service Layer Pattern

## 📁 Project Structure

```
digital_evidence_gap/
│
├── manage.py                     # Django management script
├── requirements.txt              # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore patterns
├── README.md                    # Project documentation
│
├── core/                        # Django core configuration
│   ├── __init__.py
│   ├── asgi.py                  # ASGI configuration
│   ├── wsgi.py                  # WSGI configuration
│   ├── settings.py              # Django settings (environment-aware)
│   ├── urls.py                  # Main URL configuration
│   ├── middleware.py            # Custom middleware
│   │
│
├── apps/                        # Django applications
│   │
│   ├── users/                   # User management app
│   │   ├── __init__.py, admin.py, apps.py, managers.py
│   │   ├── models.py, serializers.py, views.py, urls.py
│   │   ├── permissions.py, services.py, selectors.py, tests.py
│   │
│   ├── evidence/                # Evidence management app
│   │   ├── __init__.py, apps.py, models.py, serializers.py
│   │   ├── views.py, urls.py, services.py, selectors.py
│   │   ├── permissions.py, tests.py
│   │
│   ├── search/                  # Search functionality app
│   │   ├── __init__.py, apps.py, models.py, serializers.py
│   │   ├── views.py, urls.py, services.py, selectors.py
│   │   ├── filters.py, tests.py
│   │
│   └── common/                  # Shared utilities
│       ├── __init__.py, models.py, mixins.py, permissions.py
│       ├── pagination.py, exceptions.py, validators.py
│
├── utils/                       # Utility modules
│   ├── __init__.py, mongo_client.py, google_drive.py
│   ├── jwt_helper.py, file_utils.py, constants.py
│
├── scripts/                     # Management scripts
│   ├── create_indexes.py        # MongoDB index creation
│   └── seed_data.py             # Data seeding
│
└── docker/                      # Docker configuration
    ├── Dockerfile               # Container definition
    └── docker-compose.yml       # Multi-container setup
```

## 📋 Prerequisites

- Python 3.12.x
- MongoDB 6.0+
- Google Cloud Platform account with Drive API enabled
- Docker & Docker Compose (optional)

## 🔧 Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd digital-evidence-gap
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy the `.env` template and configure your environment variables:

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

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 5. MongoDB Setup

Ensure MongoDB is running and create the database:

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:6.0

# Or install MongoDB locally and start the service
```

### 6. Google Drive Setup

1. Create a Google Cloud Project
2. Enable Google Drive API
3. Create a Service Account
4. Download the service account key JSON file
5. Share the target Drive folder with the service account email
6. Set the `GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH` in your `.env`

### 7. Database Initialization

```bash
# Create MongoDB indexes
python scripts/create_indexes.py

# Seed initial data (optional)
python scripts/seed_data.py
```

### 8. Run Migrations (if any Django models exist)

```bash
python manage.py migrate
```

## 🚀 Running the Application

### Development Mode

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

### Production Mode

```bash
export DJANGO_ENV=production
python manage.py runserver 0.0.0.0:8000
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up --build
```

## 📚 API Documentation

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
```

**Response:**

```json
{
  "id": "evidence_id",
  "title": "Evidence Title",
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

- `q`: Search query (title search)
- `file_type`: Filter by file type (image/video)
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

## 🧪 Testing

### Run Tests

```bash
python manage.py test
```

### Run Specific App Tests

```bash
python manage.py test apps.users
python manage.py test apps.evidence
python manage.py test apps.search
```

### Coverage Report

```bash
coverage run --source='apps' manage.py test
coverage report
```

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

- **users**: User accounts and authentication data
- **evidence**: File metadata and Google Drive references
- **search_history**: User search queries and filters

### Index Management

```bash
# Create indexes
python scripts/create_indexes.py

# Indexes created:
# - users.email (unique)
# - evidence.uploaded_by
# - search_history.user_id
# - evidence.title (text index)
```

## 🔧 Development

### Code Style

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation
- Use meaningful commit messages
- Follow the existing code structure

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email support@digital-evidence-gap.com or create an issue in the repository.

## 📈 Roadmap

- [ ] API rate limiting
- [ ] File compression and optimization
- [ ] Batch upload functionality
- [ ] Advanced search filters
- [ ] Real-time notifications
- [ ] Admin dashboard
- [ ] API versioning
- [ ] Caching layer

---

**Built with ❤️ using Django REST Framework**
