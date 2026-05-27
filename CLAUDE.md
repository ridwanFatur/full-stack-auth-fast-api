# CLAUDE.md — Backend

## Project

This is the **FastAPI backend** for an **HR Management Application**.

Features:

- Google OAuth 2.0 authentication
- JWT access & refresh token management
- Multi-tenant company management (CRUD + logo upload)
- Employee management (CRUD + photo upload)
- HR modules: Attendance, Leave, Payroll, Performance (full CRUD per employee)
- Supabase Storage for file uploads (logo, employee photo, user avatar)
- Soft-delete on all entities

Architecture: **monolithic but modular**. Keep it simple; avoid overengineering.

---

## Stack

- **FastAPI** — async HTTP framework
- **SQLAlchemy** (async, `asyncpg`) — ORM
- **Alembic** — database migrations (async env)
- **PostgreSQL** — database
- **Pydantic v2** — request/response schemas
- **python-jose** — JWT
- **google-auth** — Google ID token verification
- **supabase** — file storage client
- **uv** — dependency management
- Python 3.12+

---

## Architecture

Request flow:

```
API Router → Service → Repository → Database
```

### API Layer (`app/api/v1/`)

- Request validation and response serialization only
- Dependency injection via `Depends()`
- No business logic, no direct DB queries
- Keep routes thin

### Services (`app/services/`)

All business logic lives here:

| Service | Responsibility |
|---------|---------------|
| `AuthService` | Google OAuth flow, find-or-create user, JWT issuance, logout |
| `GoogleOAuthService` | Verifies Google ID tokens; runs sync Google library calls in `run_in_executor` |
| `JWTService` | Create, verify, decode JWTs; token type claims (`"access"` / `"refresh"`) |
| `CompanyService` | Company CRUD; ownership checks; logo upload via StorageService |
| `EmployeeService` | Employee CRUD; ownership through company; photo upload via StorageService |
| `HRService` | Attendance, Leave, Payroll, Performance CRUD; `_assert_employee_access` guard; net salary auto-calc on Payroll |
| `StorageService` | Uploads files to Supabase Storage; returns public URL; `folder` param per entity type |

### Repositories (`app/repositories/`)

- Database access only — no business logic
- One repository class per model
- All methods are `async`

| Repository | Model |
|-----------|-------|
| `UserRepository` | `User` |
| `CompanyRepository` | `Company` |
| `EmployeeRepository` | `Employee` |
| `AttendanceRepository` | `Attendance` |
| `LeaveRepository` | `Leave` |
| `PayrollRepository` | `Payroll` |
| `PerformanceRepository` | `Performance` |
| `RefreshTokenRepository` | `RefreshToken` |

### Models (`app/models/`)

All models inherit `TimestampSoftDeleteMixin` from `app/models/mixins.py`:

```python
class TimestampSoftDeleteMixin:
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    is_deleted: bool  # default False
```

Always filter soft-deleted rows with `Model.is_deleted == False`. Never hard-delete.

| Model | Table | Key relationships |
|-------|-------|-------------------|
| `User` | `users` | has many `Company`, has many `RefreshToken` |
| `Company` | `companies` | belongs to `User`; has many `Employee` |
| `Employee` | `employees` | belongs to `Company`; has many `Attendance`, `Leave`, `Payroll`, `Performance` |
| `Attendance` | `attendances` | belongs to `Employee` |
| `Leave` | `leaves` | belongs to `Employee` |
| `Payroll` | `payrolls` | belongs to `Employee`; `net_salary` = `gross_salary - deductions` |
| `Performance` | `performances` | belongs to `Employee`; `rating` 1–5 |
| `RefreshToken` | `refresh_tokens` | belongs to `User`; revocable |

**Critical:** `app/models/__init__.py` imports all models so SQLAlchemy's mapper registry can resolve string-based relationships at startup. Never remove these imports.

All primary keys are `UUID`.

### Schemas (`app/schemas/`)

Pydantic v2 models for request/response. Never expose ORM models directly.

| Schema file | Contains |
|------------|---------|
| `auth.py` | `GoogleLoginRequest`, `TokenResponse`, `RefreshRequest` |
| `user.py` | `UserResponse`, `UserUpdate` |
| `company.py` | `CompanyCreate`, `CompanyUpdate`, `CompanyResponse`, `CompanyListResponse` |
| `employee.py` | `EmployeeCreate`, `EmployeeUpdate`, `EmployeeResponse`, `EmployeeListResponse` |
| `attendance.py` | `AttendanceCreate`, `AttendanceUpdate`, `AttendanceResponse` |
| `leave.py` | `LeaveCreate`, `LeaveUpdate`, `LeaveResponse` |
| `payroll.py` | `PayrollCreate`, `PayrollUpdate`, `PayrollResponse` |
| `performance.py` | `PerformanceCreate`, `PerformanceUpdate`, `PerformanceResponse` |

### Dependencies (`app/dependencies/auth.py`)

- `get_current_user` — FastAPI `Depends()` factory; reads Bearer token, verifies JWT, returns `User`

### Core (`app/core/`)

| File | Responsibility |
|------|---------------|
| `config.py` | `Settings` Pydantic BaseSettings singleton; `BACKEND_CORS_ORIGINS` parsed from JSON string |
| `database.py` | Async SQLAlchemy engine + `AsyncSession` factory; `get_db` dependency |
| `security.py` | JWT create/verify helpers |

---

## API Endpoints

All routes are prefixed `/api/v1/`.

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/auth/google/auth-url` | No | Generate Google OAuth URL + CSRF state |
| POST | `/auth/google/callback` | No | Exchange auth code → JWT (redirect flow) |
| POST | `/auth/google/login` | No | Verify Google ID token → JWT (direct flow) |
| POST | `/auth/refresh` | No | Rotate refresh token, issue new token pair |
| POST | `/auth/logout` | Bearer | Revoke refresh token |

### Users

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/users/me` | Bearer | Current user profile |
| GET | `/users/{user_id}` | Bearer | User by ID |
| POST | `/users/me/avatar` | Bearer | Upload profile picture to Supabase (`folder="avatars"`) |

### Companies

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/companies` | Bearer | List current user's companies (paginated) |
| POST | `/companies` | Bearer | Create company |
| GET | `/companies/{id}` | Bearer | Company detail |
| PUT | `/companies/{id}` | Bearer | Update company |
| DELETE | `/companies/{id}` | Bearer | Soft-delete company |
| POST | `/companies/{id}/logo` | Bearer | Upload company logo to Supabase (`folder="logos"`) |

### Employees

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/companies/{id}/employees` | Bearer | List employees (paginated) |
| POST | `/companies/{id}/employees` | Bearer | Create employee |
| GET | `/companies/{id}/employees/{eid}` | Bearer | Employee detail |
| PUT | `/companies/{id}/employees/{eid}` | Bearer | Update employee |
| DELETE | `/companies/{id}/employees/{eid}` | Bearer | Soft-delete employee |
| POST | `/companies/{id}/employees/{eid}/photo` | Bearer | Upload employee photo (`folder="photos"`) |

### HR Modules (Attendance, Leave, Payroll, Performance)

For each module `{module}` ∈ `{attendances, leaves, payrolls, performances}`:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/companies/{id}/employees/{eid}/{module}` | Bearer | List records |
| POST | `/companies/{id}/employees/{eid}/{module}` | Bearer | Create record |
| PUT | `/companies/{id}/employees/{eid}/{module}/{rid}` | Bearer | Update record |
| DELETE | `/companies/{id}/employees/{eid}/{module}/{rid}` | Bearer | Soft-delete record |

`HRService._assert_employee_access` verifies the employee belongs to a company owned by the current user before any operation.

---

## Database Migrations

Migration chain (in order):

1. `3772ce949c9b_initial_migration.py` — users, refresh_tokens, companies, employees
2. `b4e8f2a91c3d_add_hr_tables.py` — attendances, leaves, payrolls, performances
3. `c7a1d3e85f02_employee_range.py` — replaces `employee_count` (Integer) with `employee_range` (String 20)

Commands (run from `backend/`):

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

The async Alembic env (`app/migrations/env.py`) uses `async_engine_from_config`. `DATABASE_URL` must use `postgresql+asyncpg://` scheme.

---

## File Uploads — Supabase Storage

`StorageService` (`app/services/storage_service.py`) handles all uploads.

- `folder` parameter organizes files: `"logos"`, `"photos"`, `"avatars"`
- Returns the public URL stored in the corresponding model field
- Returns `503` if Supabase env vars are not configured

Required env vars:

```env
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_BUCKET=
```

---

## Domain Enums / Controlled Values

**Employee:**
- `gender`: `"male"`, `"female"` only
- `employment_status`: `"full_time"`, `"part_time"`, `"contract"`, `"intern"`, `"terminated"`

**Company:**
- `status`: `"active"`, `"inactive"`
- `employee_range`: `"1-10"`, `"10-50"`, `"50-100"`, `">100"` (optional)

**Attendance:**
- `status`: `"present"`, `"absent"`, `"late"`, `"half_day"`, `"remote"`

**Leave:**
- `leave_type`: `"annual"`, `"sick"`, `"emergency"`, `"maternity"`, `"paternity"`, `"unpaid"`
- `status`: `"pending"`, `"approved"`, `"rejected"`

**Performance:**
- `rating`: integer 1–5

---

## Code Style

- PEP8, type hints everywhere, async-first
- `snake_case` for files, functions, variables
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Services instantiated per-request by passing `AsyncSession` — no module-level DB singletons

---

## Environment Variables

```env
PROJECT_NAME=app-backend
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/app_db
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:3000/redirect/login
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
FRONTEND_URL=http://localhost:3000
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_BUCKET=
```

Never hardcode secrets. Never commit `.env`.

---

## Commands

All commands run from `backend/`.

```bash
# First-time setup
uv venv .venv
source .venv/bin/activate
uv sync

# Dev server
uvicorn app.main:app --reload

# Add dependency
uv add <package>

# Migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Sanity-check registered routes
python -c "from app.main import app; [print(list(r.methods), r.path) for r in app.routes if hasattr(r,'methods')]"
```

---

## Security Rules

- Always verify Google token server-side
- Validate JWT expiration and `"type"` claim (access/refresh not interchangeable)
- Restrict CORS via `BACKEND_CORS_ORIGINS`
- Revoke refresh token on logout
- Use HTTPS in production
- All secrets in `.env`
- Ownership guard on every company/employee/HR operation

---

## Guidance for Claude

When generating code:

- Follow existing architecture (API → Service → Repository → Database)
- Keep routes thin — no logic in routers
- Use repository pattern for all DB access
- Write async code throughout
- Add type hints to all functions
- Soft-delete only; never hard-delete
- Filter deleted rows with `Model.is_deleted == False`
- Add new models to `app/models/__init__.py`
- Run `alembic revision --autogenerate` after any model change
- Prefer **simple, maintainable, scalable** solutions
