# Authentication and role-based access control

## Authentication

The API supports short-lived signed JWT bearer tokens. Users sign in through:

`POST /api/v1/auth/token`

Request JSON:

```json
{
  "email": "operator@example.org",
  "password": "a-long-password"
}
```

A successful response contains `access_token`, `token_type`, `expires_in`, and role names. The default access-token lifetime is 30 minutes and is configurable through `ACCESS_TOKEN_EXPIRE_MINUTES`.

Passwords are hashed using Argon2id through argon2-cffi. User passwords must be at least 12 characters. Five failed password attempts trigger a 15-minute account lockout. Login errors do not reveal whether an email address exists.

Set `JWT_SECRET_KEY` to a unique random secret of at least 32 characters. `APP_SECRET_KEY` is accepted as a fallback for development compatibility, but production deployments should use a separate JWT signing secret.

## Bootstrap administrator

There is no public self-registration. The first administrator account is created by an operator using the bootstrap `ADMIN_API_TOKEN`:

`POST /api/v1/auth/users`

The bootstrap token must be at least 32 characters and should be stored only in a secret manager or protected environment file. Once the first admin account exists, administrators can create additional accounts through the administration console or API. Keep the bootstrap token available for recovery and emergency access, and rotate it periodically.

## Roles

| Role | Permissions |
|---|---|
| `admin` | Repository registry, users and roles, harvests, schedules, indexing operations, and analytics |
| `harvester` | Create/view/resume harvest jobs and manage recurring schedules |
| `viewer` | Sign in and inspect own account; public search and record discovery remain available without login |

Repository registration, user administration, indexing dispatch, and analytics remain administrator-only. The bootstrap token is treated as an administrator credential.

## User administration endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/token` | Exchange email/password for JWT |
| GET | `/api/v1/auth/me` | Inspect current account |
| POST | `/api/v1/auth/users` | Create a user (admin) |
| GET | `/api/v1/auth/users` | List users (admin) |
| PATCH | `/api/v1/auth/users/{id}/roles` | Change roles (admin) |
| PATCH | `/api/v1/auth/users/{id}/active` | Activate/deactivate account (admin) |

User creation is invitation-only. Administrators set an initial password and must communicate it securely to the user. Password reset and self-service recovery are not implemented yet.

## Audit events

Successful login, user creation, role changes, and account activation changes are written to the `audit_events` table. Bootstrap-token actions have a null user actor because the shared token is not an individual identity.

## Current limitations

- No MFA, SSO, password reset, email verification, or self-service registration.
- No refresh-token rotation or token revocation list; disabling an account blocks subsequent API requests because the user is checked on every authenticated request.
- The bootstrap token remains a shared emergency credential.
- Fine-grained per-resource permissions and individual audit attribution for bootstrap-token actions are future work.
