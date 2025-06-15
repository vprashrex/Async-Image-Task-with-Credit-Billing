# API Documentation

## Table of Contents

1. [Authentication](#authentication)
2. [Task Management](#task-management)
3. [Credit System](#credit-system)
4. [Admin Operations](#admin-operations)
5. [Error Handling](#error-handling)
6. [Security Features](#security-features)

---

## Base URL

```
http://localhost:8000
```

## Authentication

All protected endpoints require authentication via JWT tokens. Tokens can be provided either:
- In the `Authorization` header as `Bearer <token>`
- Via secure HTTP-only cookies (for web applications)

### Sign Up

**POST** `/auth/signup`

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "is_admin": false,
  "is_active": true,
  "credits": 0,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Status Codes:**
- `201` - User created successfully
- `400` - Invalid input or user already exists

### Login

**POST** `/auth/login`

Authenticate user and receive JWT tokens.

**Request Body (Form Data):**
```
username: user@example.com (email)
password: securepassword
```

**Query Parameters:**
- `remember_me`: `boolean` (optional) - Extended session duration

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Status Codes:**
- `200` - Login successful
- `401` - Invalid credentials or inactive account
- `400` - Missing email or password

### Validate Token

**POST** `/auth/validate-token`

Validate current token and return user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "is_admin": false,
    "is_active": true,
    "credits": 10
  }
}
```

**Status Codes:**
- `200` - Token is valid
- `401` - Invalid or expired token

### Refresh Token

**POST** `/auth/refresh`

Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Status Codes:**
- `200` - Token refreshed successfully
- `401` - Invalid or expired refresh token

### Logout

**POST** `/auth/logout`

Logout user and invalidate tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

**Status Codes:**
- `200` - Logout successful

---

## Task Management

### Create Task

**POST** `/tasks/`

Submit a new image processing task.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
- `file`: Image file (required)
- `title`: Task title (required, max 200 chars)
- `description`: Task description (optional, max 1000 chars)
- `processing_operation`: Processing type (default: "grayscale")

**Available Processing Operations:**
- `grayscale` - Convert to grayscale
- `blur` - Apply blur effect
- `sharpen` - Sharpen image
- `edge_detect` - Edge detection
- `invert` - Invert colors

**Response:**
```json
{
  "id": 123,
  "title": "My Image Processing Task",
  "description": "Convert my image to grayscale",
  "status": "pending",
  "original_image_url": "https://your-domain.com/files/original/image123.jpg",
  "processed_image_url": null,
  "metadata": {
    "processing_operation": "grayscale"
  },
  "error_message": null,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "completed_at": null
}
```

**Status Codes:**
- `201` - Task created successfully
- `403` - Insufficient credits
- `400` - Invalid file or input
- `401` - Authentication required

### Get User Tasks

**GET** `/tasks/`

Retrieve all tasks for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip`: `integer` (default: 0) - Number of tasks to skip
- `limit`: `integer` (default: 100) - Maximum number of tasks to return

**Response:**
```json
[
  {
    "id": 123,
    "title": "My Image Processing Task",
    "description": "Convert my image to grayscale",
    "status": "completed",
    "original_image_url": "https://your-domain.com/files/original/image123.jpg",
    "processed_image_url": "https://your-domain.com/files/processed/image123_processed.jpg",
    "metadata": {
      "processing_operation": "grayscale"
    },
    "error_message": null,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:35:00Z",
    "completed_at": "2025-01-15T10:35:00Z"
  }
]
```

**Task Statuses:**
- `pending` - Task is queued
- `processing` - Task is being processed
- `completed` - Task completed successfully
- `failed` - Task failed with error

**Status Codes:**
- `200` - Tasks retrieved successfully
- `401` - Authentication required

### Get Specific Task

**GET** `/tasks/{task_id}`

Get details of a specific task.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `task_id`: `integer` - Task ID

**Response:**
```json
{
  "id": 123,
  "title": "My Image Processing Task",
  "description": "Convert my image to grayscale",
  "status": "completed",
  "original_image_url": "https://your-domain.com/files/original/image123.jpg",
  "processed_image_url": "https://your-domain.com/files/processed/image123_processed.jpg",
  "metadata": {
    "processing_operation": "grayscale"
  },
  "error_message": null,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:35:00Z",
  "completed_at": "2025-01-15T10:35:00Z"
}
```

**Status Codes:**
- `200` - Task retrieved successfully
- `404` - Task not found
- `401` - Authentication required

### Real-time Task Updates (Server-Sent Events)

**GET** `/tasks/stream`

Subscribe to real-time task updates via Server-Sent Events.

**Headers:**
```
Accept: text/event-stream
Cache-Control: no-cache
```

**Note:** Authentication is handled via cookies for SSE connections since custom headers cannot be sent with EventSource.

**Event Types:**
```javascript
// Connection established
{
  "type": "connected",
  "message": "Connected to task updates for user 1",
  "user_id": 1
}

// Task status update
{
  "type": "task_update",
  "data": {
    "id": 123,
    "status": "completed",
    "processed_image_url": "https://your-domain.com/files/processed/image123.jpg"
  },
  "timestamp": 1642249800
}

// Heartbeat to keep connection alive
{
  "type": "heartbeat",
  "timestamp": 1642249800,
  "user_id": 1
}

// Error occurred
{
  "type": "error",
  "message": "Authentication failed",
  "timestamp": 1642249800
}
```

**Usage Example (JavaScript):**
```javascript
const eventSource = new EventSource('/tasks/stream');

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'task_update':
      console.log('Task updated:', data.data);
      break;
    case 'heartbeat':
      console.log('Connection alive');
      break;
    case 'error':
      console.error('Error:', data.message);
      break;
  }
};
```

---

## Credit System

### Get Credit Balance

**GET** `/credits/balance`

Get current credit balance for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": 1,
  "credits": 25,
  "email": "user@example.com"
}
```

**Status Codes:**
- `200` - Balance retrieved successfully
- `401` - Authentication required

### Purchase Credits

**POST** `/credits/purchase`

Create a Razorpay order for credit purchase.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "credits": 50
}
```

**Response:**
```json
{
  "order_id": "order_KJHGFDsdf5678",
  "amount": 500.0,
  "currency": "INR",
  "key": "rzp_live_xxxxxxxxxx"
}
```

**Pricing:**
- 1 Credit = ₹10 INR
- Minimum purchase: 1 credit
- Maximum purchase: 1000 credits per transaction

**Status Codes:**
- `200` - Order created successfully
- `401` - Authentication required
- `400` - Invalid credit amount

### Razorpay Webhook (Internal)

**POST** `/credits/webhook/rzp-x2394h5kjh`

Internal webhook endpoint for processing Razorpay payments. This endpoint is called by Razorpay's servers and includes advanced security measures:

- Signature verification
- Replay attack protection
- Idempotency checks
- Payload validation

**Security Features:**
- Custom webhook URL with secret path
- Request size limits (1MB)
- Timestamp validation (5-minute window)
- Event deduplication
- Comprehensive logging

---

## Admin Operations

**Note:** All admin endpoints require admin privileges (`is_admin: true`).

### Get All Users

**GET** `/admin/users`

Retrieve all users in the system (admin only).

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Query Parameters:**
- `skip`: `integer` (default: 0) - Number of users to skip
- `limit`: `integer` (default: 100) - Maximum number of users to return

**Response:**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "is_admin": false,
    "is_active": true,
    "credits": 25,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
]
```

**Status Codes:**
- `200` - Users retrieved successfully
- `401` - Authentication required
- `403` - Admin privileges required

### Get All Tasks

**GET** `/admin/tasks`

Retrieve all tasks across all users (admin only).

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Query Parameters:**
- `skip`: `integer` (default: 0) - Number of tasks to skip
- `limit`: `integer` (default: 100) - Maximum number of tasks to return

**Response:**
```json
[
  {
    "id": 123,
    "title": "User's Image Processing Task",
    "description": "Convert image to grayscale",
    "status": "completed",
    "original_image_url": "https://your-domain.com/files/original/image123.jpg",
    "processed_image_url": "https://your-domain.com/files/processed/image123_processed.jpg",
    "metadata": {
      "processing_operation": "grayscale"
    },
    "error_message": null,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:35:00Z",
    "completed_at": "2025-01-15T10:35:00Z"
  }
]
```

**Status Codes:**
- `200` - Tasks retrieved successfully
- `401` - Authentication required
- `403` - Admin privileges required

### Get Admin Statistics

**GET** `/admin/stats`

Get comprehensive system statistics (admin only).

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response:**
```json
{
  "total_users": 1250,
  "total_tasks": 5680,
  "active_users": 1100,
  "admin_users": 5
}
```

**Status Codes:**
- `200` - Statistics retrieved successfully
- `401` - Authentication required
- `403` - Admin privileges required

---

## Error Handling

### Standard Error Response Format

All error responses follow this structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- **200** - Success
- **201** - Created successfully
- **400** - Bad Request (invalid input, validation errors)
- **401** - Unauthorized (authentication required or failed)
- **403** - Forbidden (insufficient permissions or credits)
- **404** - Not Found (resource doesn't exist)
- **413** - Payload Too Large (file size exceeded)
- **422** - Unprocessable Entity (validation errors)
- **500** - Internal Server Error

### Error Examples

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Authentication Error (401):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Insufficient Credits (403):**
```json
{
  "detail": "Insufficient credits. Please purchase more credits."
}
```