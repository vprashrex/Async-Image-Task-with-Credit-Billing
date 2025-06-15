# Async - Image Processing SaaS Backend

A secure, production-ready FastAPI backend for async image processing with JWT authentication, Razorpay payments, and Celery workers.

## 🚀 Features

- **JWT Authentication** - Secure user registration and login
- **Image Processing** - Async image processing with Celery workers
- **Credit System** - Razorpay integration for credit purchases
- **Admin Dashboard** - Role-based access for admin operations
- **File Upload** - Secure image upload with validation
- **PostgreSQL** - Robust data persistence
- **Redis** - Task queue and caching
- **Docker** - Containerized deployment

## 🛠️ Tech Stack

- **FastAPI** - Modern, fast web framework
- **PostgreSQL** - Primary database with Alembic migrations
- **Redis** - Task queue and caching
- **Celery** - Async task processing
- **JWT** - Authentication tokens
- **Razorpay** - Payment processing
- **Docker** - Containerization

## 📋 Prerequisites

- Python 3.9+
- Docker & Docker Compose
- PostgreSQL (local or hosted)
- Redis
- Razorpay account

## 🔧 Setup Instructions

### 1. Quick Setup (Recommended)
```bash
# Run the setup script
python setup.py
```

### 2. Manual Setup

#### Clone and Navigate
```bash
cd virtual-space-tech-backend
```

#### Environment Setup
```bash
# Copy environment template
copy .env.example .env

# Edit .env with your credentials
```

#### Install Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

#### Option A: Local PostgreSQL with Docker (Recommended)
```bash
# Start PostgreSQL and Redis
docker-compose up -d db redis

# Run database migrations
alembic upgrade head

# Or use the setup script
python setup_database.py
```

#### Option B: Hosted PostgreSQL
1. **Get your PostgreSQL connection URL**
   - From your hosting provider (AWS RDS, Google Cloud SQL, etc.)
   

2. **Run Database Migrations**
   ```bash
   # Run migrations
   alembic upgrade head
   
   # Or use the setup script
   python setup_database.py
   ```

### 4. Start Services

#### Development Mode
```bash
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (separate terminal)
celery -A app.celery_app worker --loglevel=info

# Start Celery beat (optional, separate terminal)
celery -A app.celery_app beat --loglevel=info
```

#### Production Mode with Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## 📊 Database Migration Guide

### 1. Understanding Alembic
Alembic is the database migration tool used to manage database schema changes. All table structures are defined in Python models and migrations are automatically generated.

### 2. Migration Commands
```bash
# Check current migration status
alembic current

# Show migration history
alembic history

# Upgrade to latest migration
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Create new migration (after model changes)
alembic revision --autogenerate -m "description of changes"
```

### 3. Database Schema
The application creates these tables:
- **users** - User accounts with authentication and credits
- **tasks** - Image processing tasks with status tracking  
- **payments** - Payment records for credit purchases

### 4. Initial Setup
```bash
# Method 1: Use Alembic directly
alembic upgrade head

# Method 2: Use setup script
python setup_database.py

# Method 3: Auto-setup on app start
uvicorn app.main:app --reload
```
-- Copy content from supabase/migrations/003_create_payments_table.sql
-- Copy content from supabase/migrations/004_seed_data.sql
```

### 5. Set Up Row Level Security (RLS)
```sql
-- Enable RLS on tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (auth.uid()::text = id::text);

-- Tasks policies
CREATE POLICY "Users can view own tasks" ON tasks
  FOR SELECT USING (auth.uid()::text = user_id::text);

-- Payments policies  
CREATE POLICY "Users can view own payments" ON payments
  FOR SELECT USING (auth.uid()::text = user_id::text);
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 API Endpoints

### Authentication
- `POST /auth/signup` - Create new user account
- `POST /auth/login` - Login and get JWT token

### Tasks
- `POST /tasks/` - Submit image processing task
- `GET /tasks/` - List user's tasks
- `GET /tasks/{id}` - Get specific task details

### Credits
- `GET /credits/balance` - Get current credit balance
- `POST /credits/purchase` - Create Razorpay order
- `POST /webhook/razorpay` - Razorpay webhook handler

### Admin (Admin only)
- `GET /admin/users` - List all users
- `GET /admin/tasks` - List all tasks

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## 🐳 Docker Commands

```bash
# Build and start
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs -f app

# Rebuild specific service
docker-compose up --build app
```

## 📁 Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── celery.py           # Celery configuration
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── routes/             # API route handlers
│   ├── services/           # Business logic
│   ├── utils/              # Utility functions
│   └── workers/            # Celery workers
├── tests/                  # Test files
├── alembic/               # Database migrations
├── uploads/               # File upload directory
├── docker-compose.yml     # Docker services
├── Dockerfile            # App container
├── requirements.txt      # Python dependencies
└── .env.example         # Environment template
```

## 🔒 Security Features

- JWT token authentication
- Password hashing with bcrypt
- Input validation with Pydantic
- File type and size validation
- Razorpay webhook signature verification
- Role-based access control
- CORS configuration

## 🌍 Environment Variables

See `.env.example` for all required environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET` - JWT signing secret
- `RAZORPAY_KEY_ID` - Razorpay API key
- `RAZORPAY_KEY_SECRET` - Razorpay API secret
- `REDIS_URL` - Redis connection string