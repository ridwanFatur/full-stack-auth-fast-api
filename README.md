# App Backend

A production-ready **FastAPI monolith backend** focused on **authentication and user management**.  
Currently, this service only handles **authentication**, but it is structured to be extensible for future services while keeping a monolithic architecture.

The frontend application is managed separately and communicates with this backend through REST APIs.

---

## Features

- FastAPI monolith architecture
- Google OAuth authentication
- Google ID Token verification
- JWT-based authentication
  - Access Token
  - Refresh Token
- PostgreSQL database integration
- Alembic database migration
- User persistence
- Soft delete support
- Reusable timestamp mixin
- Environment-based configuration
- Frontend and backend separated architecture
- Ready for future module/service expansion

---

## Architecture Overview

This application follows a **monolithic backend architecture**, where all business domains live inside one backend service.

At the moment, the backend only manages:

- Authentication
- User management
- Session/token handling

In the future, additional domains can be added, such as:

- Profile management
- Notifications
- AI services
- Billing
- Analytics
- File storage
- Role & permission management

Although this is a monolith, the codebase is designed to remain modular and scalable.

---

## Authentication Flow

Authentication is handled using **Google OAuth** and **JWT**.

### Login Flow

1. User clicks **Continue with Google** from the frontend.
2. Frontend redirects the user to Google OAuth.
3. Google returns an **ID Token** to the frontend.
4. Frontend sends the token to the backend.
5. Backend verifies the Google token.
6. Backend extracts user information:
   - Name
   - Email
   - Google ID
   - Profile picture (optional)
7. Backend checks whether the user already exists.
8. If the user does not exist:
   - Create a new user record in the database.
9. Backend generates:
   - Access Token (JWT)
   - Refresh Token (JWT)
10. Tokens are returned to the frontend.

### Authentication Diagram

Frontend → Google OAuth → Google ID Token → Backend Verification → Database User → JWT Generation → Frontend

---

## Tech Stack

### Backend

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Pydantic
- JWT Authentication
- Google OAuth Verification

### Authentication

- Google OAuth 2.0
- Google ID Token Verification
- JWT Access Token
- JWT Refresh Token

### Database

- PostgreSQL

---

## Environment Variables

Create a `.env` file based on `.env.example`.

Example:

# App
PROJECT_NAME=app-backend
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Database
DATABASE_URL=postgresql://postgres:generalpassword@localhost:5432/general-db

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/redirect/login

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Frontend URL
FRONTEND_URL=http://localhost:3000

---

## Project Structure

Recommended project structure:

app/
│── api/
│   ├── v1/
│   │   ├── auth/
│   │   └── user/
│
│── core/
│   ├── config.py
│   ├── security.py
│   └── database.py
│
│── models/
│   ├── mixins.py
│   ├── user.py
│   └── refresh_token.py
│
│── schemas/
│   ├── auth.py
│   └── user.py
│
│── services/
│   ├── auth_service.py
│   ├── google_oauth_service.py
│   └── jwt_service.py
│
│── repositories/
│   ├── user_repository.py
│   └── refresh_token_repository.py
│
│── dependencies/
│   └── auth.py
│
│── migrations/
│
│── main.py

This structure helps keep the monolith modular and easier to scale.

---

## Database Design

### Base Timestamp & Soft Delete Mixin

To keep entities reusable and consistent, shared fields should be extracted into a reusable mixin.

Example reusable fields:

- `created_at`
- `updated_at`
- `deleted_at`
- `is_deleted`

Purpose:

- Track entity creation
- Track updates
- Enable soft delete
- Reuse across future tables

Recommended mixin:

`TimestampSoftDeleteMixin`

Fields:

| Field | Type | Description |
|--------|------|-------------|
| created_at | datetime | Record creation timestamp |
| updated_at | datetime | Last updated timestamp |
| deleted_at | datetime nullable | Soft delete timestamp |
| is_deleted | boolean | Soft delete status |

This mixin should be reusable across future entities.

Examples:

- User
- Roles
- Notifications
- AI Conversations
- Audit Logs

---

## User Table

The `User` table stores authenticated users from Google OAuth.

### User Entity

| Field | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| google_id | string | Google user identifier |
| email | string | User email |
| full_name | string | User name |
| profile_picture | string nullable | Profile image |
| is_active | boolean | User status |
| last_login_at | datetime nullable | Last login timestamp |
| created_at | datetime | Created timestamp |
| updated_at | datetime | Updated timestamp |
| deleted_at | datetime nullable | Deleted timestamp |
| is_deleted | boolean | Soft delete status |

### Constraints

- `email` must be unique
- `google_id` must be unique

---

## Additional Recommended Tables

Even though the current service only handles authentication, some supporting tables are recommended.

### RefreshToken Table

Used to manage refresh tokens securely.

| Field | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Relation to user |
| token | string | Refresh token |
| expires_at | datetime | Expiration date |
| revoked_at | datetime nullable | Revocation timestamp |
| created_at | datetime | Created timestamp |
| updated_at | datetime | Updated timestamp |
| deleted_at | datetime nullable | Deleted timestamp |
| is_deleted | boolean | Soft delete status |

Purpose:

- Token rotation
- Session management
- Logout support
- Revoke compromised sessions
- Multi-device login support

---

## API Endpoints

### Authentication APIs

#### Login with Google

POST `/api/v1/auth/google/login`

Description:

Authenticate user using Google OAuth token.

Request Body:

{
  "id_token": "google_id_token"
}

Response:

{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "token_type": "Bearer",
  "user": {
    "id": "uuid",
    "email": "user@email.com",
    "full_name": "John Doe"
  }
}

---

#### Refresh Access Token

POST `/api/v1/auth/refresh`

Description:

Generate a new access token using refresh token.

Request Body:

{
  "refresh_token": "jwt_refresh_token"
}

---

#### Logout

POST `/api/v1/auth/logout`

Description:

Invalidate refresh token session.

Authentication Required: Yes

---

### User APIs

#### Get Current User

GET `/api/v1/users/me`

Description:

Get authenticated user information.

Authentication Required: Yes

Response:

{
  "id": "uuid",
  "email": "user@email.com",
  "full_name": "John Doe",
  "profile_picture": "https://..."
}

---

#### Get User by ID

GET `/api/v1/users/{user_id}`

Description:

Retrieve user information by ID.

Authentication Required: Yes

---

## JWT Strategy

The backend uses **JWT authentication**.

### Access Token

Purpose:

- Used for authenticated API requests

Lifetime:

30 minutes

### Refresh Token

Purpose:

- Generate new access tokens

Lifetime:

30 days

Recommended behavior:

- Store refresh token securely
- Rotate refresh tokens
- Revoke token on logout
- Support multi-session authentication

---

## Database Migration

This project uses **Alembic** for database migration.

### Create Migration

alembic revision --autogenerate -m "initial migration"

### Apply Migration

alembic upgrade head

### Rollback Migration

alembic downgrade -1

---

## Installation

### Clone Repository

git clone <repository_url>

cd app-backend

### Create Virtual Environment

```bash
uv venv .venv
```

### Activate Environment

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
uv sync
```

## Run Application

Start development server:

uvicorn app.main:app --reload

Application URL:

http://localhost:8000

Swagger Documentation:

http://localhost:8000/docs

ReDoc Documentation:

http://localhost:8000/redoc

---

## CORS Configuration

The backend supports separated frontend architecture.

Allowed origins can be configured through:

BACKEND_CORS_ORIGINS

Example:

["http://localhost:3000"]

This allows frontend applications to communicate securely with the backend.

---

## Security Considerations

Recommended production practices:

- Never expose `.env`
- Rotate JWT secret keys periodically
- Enable HTTPS
- Store refresh tokens securely
- Validate Google ID Tokens server-side
- Restrict CORS origins
- Use database indexing for authentication fields
- Enable logging and audit tracking

---

## Current Scope

Current backend responsibility:

- Authentication only
- Google OAuth login
- JWT token management
- User persistence
- User retrieval

Not included yet:

- Authorization / RBAC
- Roles & permissions
- Email verification
- Password authentication
- Multi-factor authentication (MFA)
- User profile management

---

## Future Expansion

This monolith is designed to scale by adding domains/modules.

Possible future modules:

- User Profile
- AI Features
- Notifications
- Billing
- File Upload
- Audit Logging
- Analytics
- Admin Dashboard

The goal is to keep a **single deployable backend service** while maintaining modular internal architecture.

---

## License

This project is intended for internal or production-ready backend development and can be adapted based on project requirements.

---

## Deployment

The backend is containerised with Docker and deployed to a Google Cloud VM via **GitHub Actions** on every push to `main` that touches the `backend/` directory.

### High-level flow

1. GitHub Actions builds the Docker image and pushes it to **Google Artifact Registry** (`us-central1`).
2. The workflow SSHs into the VM, pulls the new image, and restarts the `backend` container.
3. All secrets are injected at deploy time — nothing is hardcoded.

### Create the Artifact Registry repository

Run this once before the first deployment (replace `[REPO-NAME]` with your chosen name and set it as `GAR_REPO_NAME` in GitHub Secrets):

```bash
gcloud artifacts repositories create [REPO-NAME] \
  --repository-format=docker \
  --location=us-central1 \
  --description="General Docker images"
```

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `GCP_SA_KEY` | Google Cloud Service Account JSON key (base64 or raw JSON) |
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `GAR_REPO_NAME` | Artifact Registry repository name |
| `VM_IP` | External IP address of the deployment VM |
| `SSH_USER` | SSH username on the VM |
| `SSH_PRIVATE_KEY` | SSH private key for VM access |
| `PROJECT_NAME` | Application name (`PROJECT_NAME` env var) |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins, e.g. `["https://yourapp.com"]` |
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | OAuth redirect URI registered in Google Console |
| `JWT_SECRET_KEY` | Secret key for signing JWTs |
| `JWT_ALGORITHM` | JWT algorithm (e.g. `HS256`) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime in minutes |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime in days |
| `FRONTEND_URL` | Frontend base URL (used for CORS and redirects) |