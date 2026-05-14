````markdown id="trainer-routes-md"
# Trainer Routes Documentation

## Base URL
`http://your-domain.com/api/accounts/`

## Headers Required
```http
Authorization: Bearer <trainer_access_token>
```

> **Note:** Trainers can only access data related to their linked clients.

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
    "id": 3,
    "profile_id": 1,
    "username": "trainer@example.com",
    "full_name": "John Trainer",
    "email": "trainer@example.com",
    "is_admin": false,
    "is_trainer": true,
    "is_client": false,
    "roles": ["Trainer Role"]
}
```

---

# 2. Update My Profile

**Endpoint:** `PUT /trainer/{id}/`

## Request Body

```json
{
    "specialization": "Advanced Metabolic Health",
    "bio": "Updated bio with more experience",
    "phone": "9999999999"
}
```

## cURL

```bash
curl -X PUT http://localhost:8000/api/accounts/trainer/1/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"specialization": "Advanced Metabolic Health", "bio": "Updated bio", "phone": "9999999999"}'
```

## Response (Success - 200)

```json
{
    "id": 1,
    "email": "trainer@example.com",
    "first_name": "John",
    "last_name": "Trainer",
    "full_name": "John Trainer",
    "admin_email": "admin@example.com",
    "specialization": "Advanced Metabolic Health",
    "bio": "Updated bio",
    "avatar": null,
    "phone": "9999999999",
    "is_active": true,
    "categories": [],
    "client_count": 5,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

---

# 3. List My Clients

**Endpoint:** `GET /client/?trainer={trainer_id}`

## cURL

```bash
curl -X GET "http://localhost:8000/api/accounts/client/?trainer=1" \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 200)

```json
{
    "count": 2,
    "num_pages": 1,
    "page_size": 10,
    "results": [
        {
            "client_id": 5,
            "name": "Jane Client",
            "email": "client@example.com",
            "phone": "9988776655",
            "is_active": true,
            "categories": [{"id": 1, "name": "Weight Loss"}],
            "trainer_count": 1,
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "filters": {}
}
```

---

# 4. Create Workout Plan for Client

**Endpoint:** `POST /workout-plans/create/`

## Request Body

```json
{
    "client": 5,
    "exercise": 1,
    "day_of_week": 0,
    "sets": 3,
    "reps": 10,
    "time_per_rep_seconds": 15,
    "order": 1,
    "notes": "Focus on controlled descent"
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/workout-plans/create/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"client": 5, "exercise": 1, "day_of_week": 0, "sets": 3, "reps": 10, "time_per_rep_seconds": 15, "order": 1, "notes": "Focus on controlled descent"}'
```

## Response (Success - 201)

```json
{
    "id": 1,
    "trainer": 1,
    "trainer_name": "John Trainer",
    "client": 5,
    "client_name": "Jane Client",
    "exercise": 1,
    "exercise_detail": {
        "id": 1,
        "title": "Push-up Basics",
        "video_url": "...",
        "duration_seconds": 120
    },
    "day_of_week": 0,
    "day_display": "Monday",
    "sets": 3,
    "reps": 10,
    "time_per_rep_seconds": 15,
    "order": 1,
    "notes": "Focus on controlled descent",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

---

# 5. List Workout Plans (My Clients)

**Endpoint:** `GET /workout-plans/`

## cURL

```bash
curl -X GET http://localhost:8000/api/accounts/workout-plans/ \
  -H "Authorization: Bearer <access_token>"
```

---

# 6. Update Workout Plan

**Endpoint:** `PUT /workout-plans/{id}/`

## Request Body

```json
{
    "sets": 5,
    "reps": 15,
    "time_per_rep_seconds": 20
}
```

## cURL

```bash
curl -X PUT http://localhost:8000/api/accounts/workout-plans/1/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"sets": 5, "reps": 15, "time_per_rep_seconds": 20}'
```

---

# 7. Delete Workout Plan

**Endpoint:** `DELETE /workout-plans/{id}/`

## cURL

```bash
curl -X DELETE http://localhost:8000/api/accounts/workout-plans/1/ \
  -H "Authorization: Bearer <access_token>"
```

---

# 8. Set KCAL Targets for Clients (Bulk)

**Endpoint:** `POST /kcal-targets/`

## Request Body

```json
{
    "client": [5, 6, 7],
    "day_of_week": 0,
    "target_kcal": 2000
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/kcal-targets/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"client": [5, 6, 7], "day_of_week": 0, "target_kcal": 2000}'
```

## Response (Success - 201)

```json
[
    {
        "id": 1,
        "client": 5,
        "client_email": "client1@example.com",
        "day_of_week": 0,
        "day_display": "Monday",
        "target_kcal": 2000,
        "created_by": 1,
        "created_by_email": "admin@example.com",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
]
```

---

# 9. Set Hydration Targets for Clients (Bulk)

**Endpoint:** `POST /hydration-targets/`

## Request Body

```json
{
    "client": [5, 6],
    "day_of_week": 0,
    "target_cups": 8
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/hydration-targets/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"client": [5, 6], "day_of_week": 0, "target_cups": 8}'
```

---

# 10. Set Sleep Targets for Clients (Bulk)

**Endpoint:** `POST /sleep-targets/`

## Request Body

```json
{
    "client": [5],
    "day_of_week": 1,
    "target_hours": 7.5
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/sleep-targets/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"client": [5], "day_of_week": 1, "target_hours": 7.5}'
```

---

# 11. View Clients' KCAL Logs

**Endpoint:** `GET /kcal-logs/?client={client_id}`

## cURL

```bash
curl -X GET "http://localhost:8000/api/accounts/kcal-logs/?client=5" \
  -H "Authorization: Bearer <access_token>"
```

---

# 12. View Clients' Hydration Logs

**Endpoint:** `GET /hydration-logs/?client={client_id}`

## cURL

```bash
curl -X GET "http://localhost:8000/api/accounts/hydration-logs/?client=5" \
  -H "Authorization: Bearer <access_token>"
```

---

# 13. View Clients' Sleep Logs

**Endpoint:** `GET /sleep-logs/?client={client_id}`

## cURL

```bash
curl -X GET "http://localhost:8000/api/accounts/sleep-logs/?client=5" \
  -H "Authorization: Bearer <access_token>"
```

---

# 14. Update KCAL Target (Single Client)

**Endpoint:** `PUT /kcal-targets/{id}/`

## Request Body

```json
{
    "client": [5],
    "day_of_week": 0,
    "target_kcal": 2200
}
```

## cURL

```bash
curl -X PUT http://localhost:8000/api/accounts/kcal-targets/1/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"client": [5], "day_of_week": 0, "target_kcal": 2200}'
```

---

# 15. Delete KCAL Target

**Endpoint:** `DELETE /kcal-targets/{id}/`

## cURL

```bash
curl -X DELETE http://localhost:8000/api/accounts/kcal-targets/1/ \
  -H "Authorization: Bearer <access_token>"
```

---

# End of Trainer Routes
````
