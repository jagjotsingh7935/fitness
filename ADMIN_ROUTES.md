````markdown id="admin-routes-md"
# Admin Routes Documentation

## Base URL
`http://your-domain.com/api/accounts/`

## Headers Required
```http
Authorization: Bearer <admin_access_token>
```

> **Note:** Admin can access ALL endpoints (trainer, client, etc.) but these are admin-specific.

---

# 1. Create Admin

**Endpoint:** `POST /signup/admin/`

## Request Body

```json
{
    "email": "newadmin@example.com",
    "first_name": "New",
    "last_name": "Admin"
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/signup/admin/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "newadmin@example.com", "first_name": "New", "last_name": "Admin"}'
```

## Response (Success - 201)

```json
{
    "id": 2,
    "email": "newadmin@example.com",
    "first_name": "New",
    "last_name": "Admin"
}
```

---

# 2. List All Admins

**Endpoint:** `GET /admin/?page=1&page_size=10`

## Query Parameters

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10)

## cURL

```bash
curl -X GET "http://localhost:8000/api/accounts/admin/?page=1&page_size=10" \
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
            "admin_id": 1,
            "email": "admin@example.com",
            "full_name": "Admin User",
            "date_joined": "2024-01-15T10:30:00Z",
            "last_login": "2024-01-15T10:30:00Z",
            "is_active": true
        }
    ],
    "filters": {}
}
```

---

# 3. Get Admin Details

**Endpoint:** `GET /admin/{id}/`

## cURL

```bash
curl -X GET http://localhost:8000/api/accounts/admin/1/ \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 200)

```json
{
    "id": 1,
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "full_name": "Admin User",
    "is_admin": true,
    "date_joined": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-15T10:30:00Z",
    "is_active": true
}
```

---

# 4. Update Admin

**Endpoint:** `PUT /admin/{id}/`

## Request Body

```json
{
    "first_name": "Updated",
    "last_name": "Name",
    "is_active": false
}
```

## cURL

```bash
curl -X PUT http://localhost:8000/api/accounts/admin/2/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Updated", "last_name": "Name", "is_active": false}'
```

## Response (Success - 200)

```json
{
    "id": 2,
    "email": "newadmin@example.com",
    "first_name": "Updated",
    "last_name": "Name",
    "full_name": "Updated Name",
    "is_admin": true,
    "date_joined": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-15T10:30:00Z",
    "is_active": false
}
```

---

# 5. Delete Admin

**Endpoint:** `DELETE /admin/{id}/`

## cURL

```bash
curl -X DELETE http://localhost:8000/api/accounts/admin/2/ \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 204)

```text
No Content
```

---

# 6. Create Category

**Endpoint:** `POST /categories/`

## Request Body

```json
{
    "name": "Weight Loss",
    "description": "Programs focused on healthy weight reduction",
    "is_active": true
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/categories/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Weight Loss", "description": "Weight loss programs", "is_active": true}'
```

## Response (Success - 201)

```json
{
    "id": 1,
    "name": "Weight Loss",
    "icon": null,
    "icon_url": null,
    "description": "Weight loss programs",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

---

# 7. List Categories

**Endpoint:** `GET /categories/`

## cURL

```bash
curl -X GET http://localhost:8000/api/accounts/categories/ \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 200)

```json
[
    {
        "id": 1,
        "name": "Weight Loss",
        "icon_url": null,
        "description": "Weight loss programs",
        "is_active": true,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
]
```

---

# 8. Update Category

**Endpoint:** `PUT /categories/{id}/`

## Request Body

```json
{
    "name": "Advanced Weight Loss",
    "description": "Updated description"
}
```

## cURL

```bash
curl -X PUT http://localhost:8000/api/accounts/categories/1/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Advanced Weight Loss", "description": "Updated description"}'
```

---

# 9. Delete Category

**Endpoint:** `DELETE /categories/{id}/`

## cURL

```bash
curl -X DELETE http://localhost:8000/api/accounts/categories/1/ \
  -H "Authorization: Bearer <access_token>"
```

---

# 10. Create Exercise (with video)

**Endpoint:** `POST /exercises/create/`

## Request Body (multipart/form-data)

- `title`: `"Push-up Basics"`
- `description`: `"Learn proper push-up form"`
- `duration_seconds`: `120`
- `category_ids`: `[1, 2]`
- `video`: `<file.mp4>`
- `thumbnail`: `<image.jpg>` *(optional)*

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/exercises/create/ \
  -H "Authorization: Bearer <access_token>" \
  -F "title=Push-up Basics" \
  -F "description=Learn proper push-up form" \
  -F "duration_seconds=120" \
  -F "category_ids=1" \
  -F "category_ids=2" \
  -F "video=@/path/to/video.mp4"
```

## Response (Success - 201)

```json
{
    "id": 1,
    "title": "Push-up Basics",
    "description": "Learn proper push-up form",
    "video_url": "http://localhost:8000/media/exercise_videos/video.mp4",
    "thumbnail_url": null,
    "categories": [],
    "duration_seconds": 120,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

---

# 11. List Exercises

**Endpoint:** `GET /exercises/`

## cURL

```bash
curl -X GET http://localhost:8000/api/accounts/exercises/ \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 200)

```json
[
    {
        "id": 1,
        "title": "Push-up Basics",
        "thumbnail_url": null,
        "duration_seconds": 120,
        "category_names": ["Weight Loss", "Strength"],
        "is_active": true
    }
]
```

---

# 12. Create Role

**Endpoint:** `POST /roles/`

## Request Body

```json
{
    "name": "Premium Trainer",
    "permissions": ["can_view_trainer", "update_trainer"],
    "is_staff": true,
    "is_client": false
}
```

## cURL

```bash
curl -X POST http://localhost:8000/api/accounts/roles/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Premium Trainer", "permissions": ["can_view_trainer", "update_trainer"], "is_staff": true, "is_client": false}'
```

---

# 13. List Roles

**Endpoint:** `GET /roles/`

## cURL

```bash
curl -X GET http://localhost:8000/api/accounts/roles/ \
  -H "Authorization: Bearer <access_token>"
```

## Response (Success - 200)

```json
[
    {
        "id": 1,
        "name": "Premium Trainer",
        "permissions": ["can_view_trainer", "update_trainer"],
        "is_staff": true,
        "is_client": false,
        "created_at": "2024-01-15T10:30:00Z",
        "last_updated": "2024-01-15T10:30:00Z"
    }
]
```

---

# 14. Update Role

**Endpoint:** `PUT /roles/{id}/`

## Request Body

```json
{
    "name": "Elite Trainer",
    "permissions": ["can_view_trainer", "update_trainer", "can_view_client"]
}
```

## cURL

```bash
curl -X PUT http://localhost:8000/api/accounts/roles/1/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Elite Trainer", "permissions": ["can_view_trainer", "update_trainer", "can_view_client"]}'
```

---

# 15. Delete Role

**Endpoint:** `DELETE /roles/{id}/`

## cURL

```bash
curl -X DELETE http://localhost:8000/api/accounts/roles/1/ \
  -H "Authorization: Bearer <access_token>"
```

---

# End of Admin Routes
````
