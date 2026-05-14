````markdown
# Authentication & OTP Routes

**Base URL:** `http://your-domain.com/api/accounts/`

---

# 1. Login (Email/Password)

**Endpoint:** `POST /login/`

## Request Body

```json
{
    "username": "user@example.com",
    "password": "password123"
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@example.com", "password": "password123"}'
```

## Response (Success - 200)

```json
{
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
        "id": 1,
        "profile_id": 1,
        "username": "admin@example.com",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "is_admin": true,
        "is_trainer": false,
        "is_client": false,
        "roles": []
    }
}
```

## Response (Error - 401)

```json
{
    "detail": "No active account found with the given credentials"
}
```

---

# 2. Refresh Token

**Endpoint:** `POST /token/refresh/`

## Request Body

```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your_refresh_token"}'
```

## Response (Success - 200)

```json
{
    "access": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

# 3. Verify Token

**Endpoint:** `POST /token/verify/`

## Request Body

```json
{
    "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/token/verify/ \
  -H "Content-Type: application/json" \
  -d '{"token": "your_access_token"}'
```

## Response (Success - 200)

```json
{
    "detail": "Token is valid"
}
```

---

# 4. Get Current User

**Endpoint:** `GET /me/`

## Headers

```http
Authorization: Bearer <access_token>
```

## cURL

```bash
curl -X GET http://localhost:8000/api/accounts/me/ \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 200)

```json
{
    "id": 1,
    "profile_id": 1,
    "username": "admin@example.com",
    "full_name": "Admin User",
    "email": "admin@example.com",
    "is_admin": true,
    "is_trainer": false,
    "is_client": false,
    "roles": ["Admin Role"]
}
```

---

# 5. Logout

**Endpoint:** `POST /logout/`

## Headers

```http
Authorization: Bearer <access_token>
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/logout/ \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 205)

```json
{
    "detail": "Successfully logged out"
}
```

---

# 6. Request OTP (Passwordless Login)

**Endpoint:** `POST /request-otp/`

## Request Body

```json
{
    "email": "client@example.com"
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/request-otp/ \
  -H "Content-Type: application/json" \
  -d '{"email": "client@example.com"}'
```

## Response (Success - 200)

```json
{
    "message": "OTP sent to email"
}
```

---

# 7. Verify OTP

**Endpoint:** `POST /verify-otp/`

## Request Body

```json
{
    "email": "client@example.com",
    "otp": "123456"
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"email": "client@example.com", "otp": "123456"}'
```

## Response (Success - 200)

```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIs...",
    "access": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
        "id": 5,
        "profile_id": 5,
        "username": "client@example.com",
        "full_name": "Jane Client",
        "email": "client@example.com",
        "is_admin": false,
        "is_trainer": false,
        "is_client": true,
        "roles": []
    }
}
```

## Response (Error - 400)

```json
{
    "error": "Invalid or expired OTP"
}
```

---

# End of Auth Routes
````
