# Expense Manager

A personal expense/income tracking API built with **FastAPI**, **SQLAlchemy** (async), and **Alembic**.

## Tech Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: SQLite (default) / PostgreSQL (via `asyncpg`)
- **Migrations**: Alembic
- **Auth**: JWT (via `python-jose`) + password hashing (via `passlib`)
- **Validation**: Pydantic v2

## Prerequisites

- Python 3.10+
- pip

## Setup

### 1. Clone and enter the project

```bash
cd expense-manager
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
# or venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=sqlite+aiosqlite:///./expense.db
JWT_SECRET=your-secret-key-change-this
```

> `DATABASE_URL` defaults to `sqlite+aiosqlite:///./expense.db` if not set.  
> `JWT_SECRET` is **required** and has no default.

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs at `http://localhost:8000/docs`.

## Project Structure

```
expense-manager/
├── app/
│   ├── main.py              # FastAPI app entry point (health endpoint only)
│   ├── config.py            # Pydantic settings (DB, JWT)
│   ├── database.py          # Async engine + session factory
│   ├── dependencies.py      # Shared FastAPI dependencies
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── category.py
│   │   └── transaction.py   # Incomplete — columns not yet defined
│   ├── schemas/             # Pydantic request/response schemas (empty - TODO)
│   ├── routers/             # API route handlers (empty - TODO)
│   ├── services/            # Business logic (empty - TODO)
│   └── utils/               # Utility functions (empty - TODO)
├── alembic/
│   ├── env.py               # Alembic async configuration
│   └── versions/
│       ├── f27f93e88c12_create_users_table.py    # Creates `users` table
│       └── ce6911ae2967_create_categories_table.py  # Stub - no actual migration
├── alembic.ini
├── requirements.txt
└── README.md
```

## Database Models

### User (`users` table)
| Column           | Type         | Notes                  |
|------------------|--------------|------------------------|
| id               | UUID (PK)    | auto-generated         |
| email            | String       | unique, indexed        |
| hashed_password  | String       |                        |
| full_name        | String?      | nullable               |
| is_active        | Boolean      | default `true`         |
| created_at       | DateTime(tz) | server default now()   |
| updated_at       | DateTime(tz) | on update now()        |

### Category (`categories` table)
| Column     | Type         | Notes                        |
|------------|--------------|------------------------------|
| id         | UUID (PK)    | auto-generated               |
| name       | String       | indexed                      |
| type       | String       | "expense" or "income"        |
| is_active  | Boolean      | default `true`               |
| user_id    | UUID (FK)    | references `users.id`        |
| created_at | DateTime(tz) | server default now()         |

Unique constraint on `(user_id, name, type)`.

### Transaction (`transactions` table)
⚠️ **Not yet implemented** — the model file exists but has no columns defined.

## API Endpoints

| Method | Path  | Description         | Status     |
|--------|-------|---------------------|------------|
| GET    | `/`   | Health check        | ✅ Done    |
| —      | —     | User auth endpoints | ❌ TODO    |
| —      | —     | Category CRUD       | ❌ TODO    |
| —      | —     | Transaction CRUD    | ❌ TODO    |

## Current Status

This project is in early development. The following is **not yet implemented**:

- [ ] Pydantic schemas (request/response models)
- [ ] API routers (auth, categories, transactions)
- [ ] JWT authentication & authorization
- [ ] Business logic layer (services)
- [ ] Transaction model columns & migration
- [ ] Categories migration is a stub — must be re-generated
- [ ] Alembic env needs to import all models (currently imports `User` only)

## License

MIT