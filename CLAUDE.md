# CLAUDE.md

## Project

This repository is a **FastAPI modular monolith backend** focused on **authentication and user management**.

Current features:

- Google OAuth login
- Google ID Token verification
- JWT authentication
- Refresh token flow
- User persistence

Frontend is separated and communicates via REST API.

Keep the architecture **monolithic but modular**.

Avoid overengineering.

---

## Stack

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Pydantic
- JWT
- Google OAuth
- uv

Python:

- 3.11+

---

## Architecture

Follow this flow:

```text
API → Service → Repository → Database
```

Responsibilities:

### API

- request validation
- response serialization
- dependency injection

Avoid:

- business logic
- database queries

Keep routes thin.

### Services

Responsible for:

- authentication logic
- Google token verification
- JWT generation
- business logic

### Repositories

Responsible for:

- database access
- CRUD operations
- query abstraction

No business logic.

### Models

Responsible for:

- schema
- relationships
- constraints

---

## Structure

Prefer:

```text
app/
├── api/
├── core/
├── models/
├── schemas/
├── repositories/
├── services/
├── dependencies/
├── migrations/
└── main.py
```

Rules:

- `services/` for business logic
- `repositories/` for DB logic
- `core/` for shared utilities
- avoid circular dependencies

---

## Authentication

Flow:

```text
Frontend
→ Google OAuth
→ ID Token
→ Backend Verification
→ Find/Create User
→ JWT Generation
→ Frontend
```

Backend must:

- verify Google token server-side
- create user if not exists
- issue access token
- issue refresh token
- persist refresh session

JWT:

Access token:

- 30 minutes

Refresh token:

- 30 days
- revocable
- multi-device friendly

---

## Database

Use PostgreSQL.

Prefer UUID primary keys.

All entities should inherit:

```python
TimestampSoftDeleteMixin
```

Fields:

- created_at
- updated_at
- deleted_at
- is_deleted

Prefer soft delete.

Do not hard delete unless explicitly required.

---

## API Rules

Use versioning:

```text
/api/v1/
```

Examples:

```text
/api/v1/auth/google/login
/api/v1/auth/refresh
/api/v1/users/me
```

Always use Pydantic schemas.

Never expose ORM models directly.

---

## Code Style

Follow:

- PEP8
- type hints
- async-first patterns
- reusable functions
- explicit naming

Naming:

Files:

```text
snake_case.py
```

Classes:

```text
PascalCase
```

Functions & variables:

```text
snake_case
```

Constants:

```text
UPPER_SNAKE_CASE
```

Prefer:

```python
async def get_current_user(
    db: AsyncSession,
    user_id: UUID
) -> User:
    ...
```

Avoid:

```python
def getUser(x):
    ...
```

---

## Environment

Configuration must come from `.env`.

Never hardcode:

- secrets
- credentials
- URLs
- JWT keys

Required env:

```env
DATABASE_URL=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
FRONTEND_URL=
BACKEND_CORS_ORIGINS=
```

---

## Dependencies

Use **uv only**.

Setup:

```bash
uv venv .venv
source .venv/bin/activate
uv sync
```

Add dependency:

```bash
uv add fastapi
```

Avoid:

- pip
- poetry
- pipenv

---

## Migration

Use Alembic only.

Create:

```bash
alembic revision --autogenerate -m "create user table"
```

Apply:

```bash
alembic upgrade head
```

Rollback:

```bash
alembic downgrade -1
```

---

## Security

Always:

- verify Google token server-side
- validate JWT expiration
- restrict CORS
- revoke refresh token on logout
- use HTTPS in production
- store secrets in `.env`

Never:

- trust frontend auth
- commit `.env`
- hardcode secrets

---

## Guidance For Claude

When generating code:

- follow existing architecture
- keep routes thin
- use repository pattern
- write async code
- add type hints
- keep code modular
- avoid unnecessary abstraction
- keep code production-ready

Prefer solutions that are:

**simple, maintainable, scalable**