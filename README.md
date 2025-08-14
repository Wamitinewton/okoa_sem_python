# Study App Backend - FastAPI + YouTube Integration

A comprehensive FastAPI backend for a study application with YouTube video integration, featuring video bookmarking, note-taking, and playlist management.

## 🚀 Features

### Core Functionality
- **YouTube Integration**: Search and save educational videos
- **Video Management**: Save, categorize, and track watch progress
- **Smart Note-Taking**: Timestamped notes linked to specific video moments
- **Playlist System**: Organize videos into custom study playlists
- **User Authentication**: JWT-based secure authentication
- **Progress Tracking**: Monitor study progress and watch time

### Technical Features
- **FastAPI Framework**: High-performance async API
- **PostgreSQL Database**: Robust data persistence
- **Redis Caching**: Fast data retrieval and session management
- **SQLAlchemy ORM**: Type-safe database operations
- **Alembic Migrations**: Database schema versioning
- **Docker Support**: Easy deployment and development
- **Comprehensive API Documentation**: Auto-generated OpenAPI docs

## 🏗️ Project Structure

```
study_app_backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py          # Application configuration
│   │   ├── database.py        # Database connection setup
│   │   └── security.py        # Authentication utilities
│   ├── api/v1/
│   │   └── endpoints/
│   │       ├── auth.py        # Authentication endpoints
│   │       ├── videos.py      # Video management endpoints
│   │       ├── notes.py       # Note-taking endpoints
│   │       └── playlists.py   # Playlist management endpoints
│   ├── models/                # SQLAlchemy database models
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/
│   │   └── youtube_service.py # YouTube API integration
│   └── utils/                 # Helper utilities
├── scripts/                   # Database and setup scripts
├── docker-compose.yml         # Docker services configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- YouTube Data API v3 key

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd study_app_backend
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your configurations
```

Required environment variables:
```env
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=studyapp

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-super-secret-key-here
YOUTUBE_API_KEY=your-youtube-api-key

# CORS (for frontend)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 3. Database Setup
```bash
# Automated setup (recommended)
make setup

# Or manual setup
python scripts/setup_database.py
python scripts/seed_data.py
```

### 4. Run Development Server
```bash
# Using make
make dev

# Or directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🐳 Docker Setup

### Quick Start with Docker
```bash
# Start all services
make docker-run

# Or manually
docker-compose up -d
```

### Services
- **API Server**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 📚 API Documentation

Once the server is running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 API Endpoints Overview

### Authentication
```
POST   /api/v1/auth/register     # Register new user
POST   /api/v1/auth/login        # User login
GET    /api/v1/auth/me          # Get current user info
```

### Video Management
```
GET    /api/v1/videos/search           # Search YouTube videos
GET    /api/v1/videos/search/educational # Search educational content
POST   /api/v1/videos/save            # Save video to library
GET    /api/v1/videos/saved           # Get saved videos
PUT    /api/v1/videos/saved/{id}      # Update video progress
DELETE /api/v1/videos/saved/{id}      # Remove saved video
```

### Notes
```
POST   /api/v1/notes/              # Create study note
GET    /api/v1/notes/              # Get user notes
GET    /api/v1/notes/{id}          # Get specific note
PUT    /api/v1/notes/{id}          # Update note
DELETE /api/v1/notes/{id}          # Delete note
```

### Playlists
```
POST   /api/v1/playlists/                    # Create playlist
GET    /api/v1/playlists/                    # Get user playlists
GET    /api/v1/playlists/{id}               # Get playlist with videos
POST   /api/v1/playlists/{id}/videos        # Add video to playlist
DELETE /api/v1/playlists/{id}/videos/{vid}  # Remove video from playlist
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
make test
# or
pytest tests/ -v
```

## 🔧 Development Commands

```bash
# Install dependencies
make install

# Run development server
make dev

# Database operations
make migrate          # Run migrations
make seed            # Seed sample data
make db-reset        # Reset database completely

# Docker operations
make docker-build    # Build containers
make docker-run      # Run with docker-compose
make docker-logs     # View logs
make docker-stop     # Stop containers

# Cleanup
make clean           # Remove cache files
```

## 🎯 Key Features Deep Dive

### YouTube Integration
- **Smart Search**: Educational content prioritization
- **Metadata Extraction**: Automatic title, description, duration extraction
- **Thumbnail Caching**: Improved performance with cached thumbnails
- **API Rate Limiting**: Efficient quota management

### Study Progress Tracking
- **Watch Progress**: Percentage-based progress tracking
- **Time Analytics**: Total watch time per video
- **Study Sessions**: Track learning sessions and patterns
- **Category Organization**: Custom categorization system

### Note-Taking System
- **Timestamp Linking**: Notes tied to specific video moments
- **Tag System**: Organize notes with custom tags
- **Search Functionality**: Find notes across all videos
- **Export Options**: Backup and export study notes

### Playlist Management
- **Custom Playlists**: Organize videos by topic/subject
- **Order Management**: Custom video ordering within playlists
- **Sharing Ready**: Foundation for playlist sharing features
- **Progress Tracking**: Monitor completion across playlists

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt password security
- **CORS Configuration**: Controlled cross-origin access
- **Input Validation**: Pydantic schema validation
- **SQL Injection Protection**: SQLAlchemy ORM protection

## 📊 Database Schema

### Core Tables
- **users**: User authentication and profile data
- **saved_videos**: User's saved YouTube videos with metadata
- **study_notes**: Timestamped notes linked to videos
- **playlists**: User-created video collections
- **playlist_videos**: Many-to-many playlist-video relationships

## 🚀 Production Deployment

### Environment Setup
1. Set production environment variables
2. Configure PostgreSQL and Redis instances
3. Set up reverse proxy (nginx recommended)
4. Configure SSL certificates
5. Set up monitoring and logging

### Docker Production
```bash
# Build production image
docker build -t studyapp-backend .

# Run with production docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the API documentation at `/docs`
- Review the codebase for implementation details

## 🎉 Sample Data

The application includes sample data for testing:
- **Demo User**: `demo@studyapp.com` / `demopassword`
- **Sample Videos**: 3 educational videos across different categories
- **Sample Notes**: Example timestamped notes
- **Sample Playlist**: Programming fundamentals collection

Run `make seed` to populate your database with this sample data.

---

**Happy Learning! 📚✨**