````markdown id="client-routes-md"
# Client Routes Documentation

## Base URL
`http://your-domain.com/api/accounts/`

## Headers Required
```http
Authorization: Bearer <client_access_token>
```

---

# 1. Get My Profile

**Endpoint:** `GET /me/`

## cURL

```bash
curl -X GET http://localhost:8000/api/accounts/me/ \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 200)

```json
{
    "id": 5,
    "profile_id": 1,
    "username": "client@example.com",
    "full_name": "Jane Client",
    "email": "client@example.com",
    "is_admin": false,
    "is_trainer": false,
    "is_client": true,
    "roles": []
}
```

---

# 2. Update My Profile

**Endpoint:** `PUT /client/{id}/`

## Request Body

```json
{
    "phone": "9999999999",
    "address": "456 New Address",
    "date_of_birth": "1990-05-15"
}
```

## cURL

```bash
curl -X PUT http://localhost:8000/api/accounts/client/1/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"phone": "9999999999", "address": "456 New Address", "date_of_birth": "1990-05-15"}'
```

## Response (Success - 200)

```json
{
    "id": 1,
    "email": "client@example.com",
    "first_name": "Jane",
    "last_name": "Client",
    "full_name": "Jane Client",
    "date_of_birth": "1990-05-15",
    "phone": "9999999999",
    "address": "456 New Address",
    "is_active": true,
    "categories": [],
    "active_trainers": [
        {
            "id": 1,
            "name": "John Trainer",
            "specialization": "Weight Loss Expert"
        }
    ],
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

---

# 3. Get My Workout Plans (Grouped by Day)

**Endpoint:** `GET /my-workout-plans/`

## cURL

```bash
curl -X GET http://localhost:8000/api/accounts/my-workout-plans/ \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 200)

```json
[
    {
        "id": 1,
        "day_of_week": 0,
        "day_display": "Monday",
        "order": 1,
        "exercise_detail": {
            "id": 1,
            "title": "Push-up Basics",
            "video_url": "http://localhost:8000/media/exercise_videos/pushup.mp4",
            "thumbnail_url": null,
            "duration_seconds": 120,
            "description": "Learn proper push-up form"
        },
        "sets": 3,
        "reps": 10,
        "time_per_rep_seconds": 15,
        "notes": "Focus on controlled descent"
    },
    {
        "id": 2,
        "day_of_week": 0,
        "day_display": "Monday",
        "order": 2,
        "exercise_detail": {
            "id": 2,
            "title": "Squats",
            "video_url": "http://localhost:8000/media/exercise_videos/squats.mp4",
            "duration_seconds": 90,
            "description": "Proper squat form"
        },
        "sets": 4,
        "reps": 12,
        "time_per_rep_seconds": 10,
        "notes": "Keep back straight"
    }
]
```

---

# 4. Log KCAL Burned

**Endpoint:** `POST /kcal-logs/`

## Request Body

```json
{
    "date": "2025-05-10",
    "actual_kcal": 1850,
    "notes": "Evening run 5km"
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/kcal-logs/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-05-10", "actual_kcal": 1850, "notes": "Evening run 5km"}'
```

## Response (Success - 201)

```json
{
    "id": 1,
    "client": 5,
    "client_email": "client@example.com",
    "date": "2025-05-10",
    "actual_kcal": 1850,
    "notes": "Evening run 5km",
    "created_at": "2025-05-10T10:30:00Z",
    "updated_at": "2025-05-10T10:30:00Z"
}
```

---

# 5. Get KCAL Summary (Target vs Actual)

**Endpoint:** `GET /kcal-summary/?start_date=2025-05-05&end_date=2025-05-11`

## Query Parameters

- `start_date`: `YYYY-MM-DD` (optional, defaults to Monday of current week)
- `end_date`: `YYYY-MM-DD` (optional, defaults to Sunday of current week)

## cURL

```bash
curl -X GET "http://localhost:8000/api/accounts/kcal-summary/?start_date=2025-05-05&end_date=2025-05-11" \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 200)

```json
[
    {
        "date": "2025-05-05",
        "day": "Monday",
        "target_kcal": 2000,
        "actual_kcal": 1850,
        "achieved": false
    },
    {
        "date": "2025-05-06",
        "day": "Tuesday",
        "target_kcal": 1800,
        "actual_kcal": 1900,
        "achieved": true
    },
    {
        "date": "2025-05-07",
        "day": "Wednesday",
        "target_kcal": 1800,
        "actual_kcal": null,
        "achieved": null
    }
]
```

---

# 6. Log Hydration

**Endpoint:** `POST /hydration-logs/`

## Request Body

```json
{
    "date": "2025-05-10",
    "actual_cups": 6,
    "notes": "Drank 2 liters"
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/hydration-logs/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-05-10", "actual_cups": 6, "notes": "Drank 2 liters"}'
```

## Response (Success - 201)

```json
{
    "id": 1,
    "client": 5,
    "client_email": "client@example.com",
    "date": "2025-05-10",
    "actual_cups": 6,
    "notes": "Drank 2 liters",
    "created_at": "2025-05-10T10:30:00Z",
    "updated_at": "2025-05-10T10:30:00Z"
}
```

---

# 7. Get My Hydration Logs

**Endpoint:** `GET /hydration-logs/`

## cURL

```bash
curl -X GET http://localhost:8000/api/accounts/hydration-logs/ \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 200)

```json
[
    {
        "id": 1,
        "client": 5,
        "client_email": "client@example.com",
        "date": "2025-05-10",
        "actual_cups": 6,
        "notes": "Drank 2 liters",
        "created_at": "2025-05-10T10:30:00Z",
        "updated_at": "2025-05-10T10:30:00Z"
    }
]
```

---

# 8. Log Sleep

**Endpoint:** `POST /sleep-logs/`

## Request Body

```json
{
    "date": "2025-05-10",
    "actual_hours": 6.5,
    "notes": "Woke up once"
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/sleep-logs/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-05-10", "actual_hours": 6.5, "notes": "Woke up once"}'
```

## Response (Success - 201)

```json
{
    "id": 1,
    "client": 5,
    "client_email": "client@example.com",
    "date": "2025-05-10",
    "actual_hours": 6.5,
    "notes": "Woke up once",
    "created_at": "2025-05-10T10:30:00Z",
    "updated_at": "2025-05-10T10:30:00Z"
}
```

---

# 9. Get My Sleep Logs

**Endpoint:** `GET /sleep-logs/`

## cURL

```bash
curl -X GET http://localhost:8000/api/accounts/sleep-logs/ \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 200)

```json
[
    {
        "id": 1,
        "client": 5,
        "client_email": "client@example.com",
        "date": "2025-05-10",
        "actual_hours": 6.5,
        "notes": "Woke up once",
        "created_at": "2025-05-10T10:30:00Z",
        "updated_at": "2025-05-10T10:30:00Z"
    }
]
```

---

# 10. Update KCAL Log (Fix Wrong Entry)

**Endpoint:** `PUT /kcal-logs/{id}/`

## Request Body

```json
{
    "date": "2025-05-10",
    "actual_kcal": 1950,
    "notes": "Actually ran 6km"
}
```

## cURL

```bash
curl -X PUT http://localhost:8000/api/accounts/kcal-logs/1/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-05-10", "actual_kcal": 1950, "notes": "Actually ran 6km"}'
```

---

# 11. Update Hydration Log

**Endpoint:** `PUT /hydration-logs/{id}/`

## Request Body

```json
{
    "date": "2025-05-10",
    "actual_cups": 7,
    "notes": "Drank 2.5 liters"
}
```

---

# 12. Update Sleep Log

**Endpoint:** `PUT /sleep-logs/{id}/`

## Request Body

```json
{
    "date": "2025-05-10",
    "actual_hours": 7.0,
    "notes": "Slept better"
}
```

---

# 13. Delete KCAL Log

**Endpoint:** `DELETE /kcal-logs/{id}/`

## cURL

```bash
curl -X DELETE http://localhost:8000/api/accounts/kcal-logs/1/ \
  -H "Authorization: Bearer <access_token>"
```

---

# 14. Delete Hydration Log

**Endpoint:** `DELETE /hydration-logs/{id}/`

## cURL

```bash
curl -X DELETE http://localhost:8000/api/accounts/hydration-logs/1/ \
  -H "Authorization: Bearer <access_token>"
```

---

# 15. Delete Sleep Log

**Endpoint:** `DELETE /sleep-logs/{id}/`

## cURL

```bash
curl -X DELETE http://localhost:8000/api/accounts/sleep-logs/1/ \
  -H "Authorization: Bearer <access_token>"
```

---

# End of Client Routes
````
