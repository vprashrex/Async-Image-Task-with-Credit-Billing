# 🚀 Async Image Processing SaaS Backend

A production-ready backend built with **FastAPI** for secure and scalable **asynchronous image processing**, featuring:

* 🔐 JWT-based authentication
* 💳 Razorpay payments
* 🐇 Celery workers
* 🚀 Redis queueing
* 🐳 Docker support

---

## 🧰 Tech Stack

| Tool          | Purpose                                             |
| ------------- | --------------------------------------------------- |
| ⚡ FastAPI     | Web framework for building APIs                     |
| 🐘 PostgreSQL | Primary relational database with Alembic migrations |
| 🚀 Redis      | Caching and task queue broker                       |
| 🐇 Celery     | Background job processing engine                    |
| 🔐 JWT        | Token-based authentication                          |
| 💳 Razorpay   | Payment integration                                 |
| 🐳 Docker     | Containerization for easy deployment                |

---

## 📦 Prerequisites

Make sure you have the following installed:

* Python 3.9+
* Docker & Docker Compose
* PostgreSQL (local or remote)
* Redis
* Razorpay account

---

## ⚙️ Setup Instructions

### 🔁 Quick Start

#### 🔷 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

➡️ Visit: [http://localhost:3000](http://localhost:3000)

---

#### 🐍 Backend Setup (Python)

```bash
cd backend
# Create virtual environment
python -m venv venv
```

```bash
# Activate environment
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

```bash
# Install Python dependencies
pip install -r requirements.txt
```

```bash
# Setup PostgreSQL schema and seed data
python setup_database.py
```

---

## 🔃 Redis Setup

Pick your platform:

### 🪟 Windows

👉 Download Redis:
[Redis for Windows Installer](https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.msi)

---

### 🐳 Docker (Recommended)

```bash
docker run -d --name redis-alpine -p 6379:6379 redis:alpine
```

---

### 🐧 Ubuntu (or WSL)

```bash
sudo apt update && sudo apt install redis-server -y
sudo service redis-server start
redis-cli ping  # Should return PONG
```

---

## ▶️ Running the Application

### 🚀 Backend (FastAPI)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 🧵 Celery Workers

#### 🪟 Windows

```bash
celery -A app.celery_app worker --loglevel=info --pool=eventlet
celery -A app.celery_app beat --loglevel=info  # For scheduled tasks
```

#### 🐧 Linux/macOS

```bash
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat --loglevel=info
```

---

## 🛢️ Database Migration Guide

Alembic handles schema migrations.

### 🔁 Common Commands

```bash
# Show current state
alembic current

# See history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Autogenerate a new migration
alembic revision --autogenerate -m "Your message"
```

---

### 📋 Schema Overview

| Table      | Purpose                         |
| ---------- | ------------------------------- |
| `users`    | Handles authentication, credits |
| `tasks`    | Tracks image processing jobs    |
| `payments` | Records Razorpay transactions   |

---

### 🧪 Initial Setup Options

```bash
# Option 1: Run Alembic directly
alembic upgrade head

# Option 2: Use Python setup script
python setup_database.py

# Option 3: Let app auto-create on launch
uvicorn app.main:app --reload
```

💡 Using Supabase?
Include SQL from:

* `supabase/migrations/003_create_payments_table.sql`
* `supabase/migrations/004_seed_data.sql`

---

## 🔐 Supabase Row Level Security (RLS)

```sql
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Define policies
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can view own tasks" ON tasks
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can view own payments" ON payments
  FOR SELECT USING (auth.uid()::text = user_id::text);
```

---

## 📖 API Documentation

Once FastAPI is running, explore:

* 🧪 **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* 📘 **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

📂 Additional Docs:

* `./backend/docs/APIDocs.md`
* `./backend/docs/Deploy.md`
* `./backend/docs/Security.md`

---

## ✅ Final Notes

* Make sure to configure `.env` for production with secure values.
* Add HTTPS, secure CORS policies, and disable debug mode before deployment.
* Deploy easily to **Render**, **Railway**, **Heroku**, or Docker-based platforms.

---

Let me know if you want to add:

* Screenshots of the frontend
* Postman collection
* Deployment instructions using Docker Compose or Railway CLI