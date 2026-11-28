# Authentication & Store Management API Testing Guide

> **Note:** Registration creates **only a user account**. After logging in, the user can create a store, and the first member of that store is automatically assigned the `owner` role. Email verification remains removed.

---

## 1. Start the API

From the `backend` directory, apply the migrations and start the development server:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

### Postman Setup
* **Base URL:** `http://127.0.0.1:8000`
* **Header:** `Content-Type: application/json`

---

## 2. Test Flow

### Step 1: Register a User
* **Endpoint:** `POST /auth/register`
* **Body:**
  ```json
  {
    "email": "owner@example.com",
    "password": "a-long-test-password"
  }
  ```
* **Expected Result:** Returns `201 Created` and a user ID. No store name or address is needed.

---

### Step 2: Confirm Store Creation Requires Login
* **Endpoint:** `POST /stores`
* **Authorization:** None
* **Body:**
  ```json
  {
    "name": "Test Shop",
    "address": "Kathmandu"
  }
  ```
* **Expected Result:** Returns `401 Unauthorized`.

---

### Step 3: Log In
* **Endpoint:** `POST /auth/login`
* **Body:**
  ```json
  {
    "email": "owner@example.com",
    "password": "a-long-test-password"
  }
  ```
* **Expected Result:** Returns an `access_token` and a `refresh_token`.
* **Postman Action:** Go to **Authorization → Bearer Token** and paste the `access_token`.

---

### Step 4: Create the Store
* **Endpoint:** `POST /stores`
* **Authorization:** `Bearer <access_token>`
* **Body:**
  ```json
  {
    "name": "Test Shop",
    "address": "Kathmandu"
  }
  ```
* **Expected Result:** Returns the store ID and `"role": "owner"`.

---

### Step 5: Check the Protected User Route
* **Endpoint:** `GET /auth/me`
* **With Token (`Bearer <access_token>`):** Expect the logged-in user's ID and email.
* **Without Token:** Remove the token and resend → Expect `401 Unauthorized`.

---

### Step 6: Refresh Tokens
* **Endpoint:** `POST /auth/refresh`
* **Body:**
  ```json
  {
    "refresh_token": "paste-refresh-token-here"
  }
  ```
* **Expected Result:** Returns new `access_token` and `refresh_token` values.
* **Verification & Action:**
  * Confirm the previous `refresh_token` and its paired `access_token` no longer work.
  * Replace both tokens in Postman with the new pair.

---

### Step 7: Log Out
* **Endpoint:** `POST /auth/logout`
* **Authorization:** `Bearer <current_access_token>`
* **Body:**
  ```json
  {
    "refresh_token": "paste-current-refresh-token-here"
  }
  ```
* **Verification:** Retry `GET /auth/me` with that access token → Expect `401 Unauthorized`.

---

### Step 8: Test Password Reset
1. **Request Reset:** `POST /auth/password-reset/request`
   ```json
   {
     "email": "owner@example.com"
   }
   ```
2. **Copy Token:** Copy the reset token from the backend terminal.
3. **Confirm Reset:** `POST /auth/password-reset/confirm`
   ```json
   {
     "token": "paste-reset-token-here",
     "new_password": "a-different-long-password"
   }
   ```
* **Expected Result:**
  * Logging in with the old password fails.
  * Logging in with the new password succeeds.
  * Password reset revokes all existing sessions.

---

## 3. Quick Verification Checklist

| Step | Endpoint | Auth Required | Expected Outcome |
| :--- | :--- | :--- | :--- |
| 1. Register | `POST /auth/register` | No | `201 Created` + user ID |
| 2. Unauth Store | `POST /stores` | No | `401 Unauthorized` |
| 3. Login | `POST /auth/login` | No | `200 OK` + access & refresh tokens |
| 4. Create Store | `POST /stores` | Bearer Token | Store ID + `"role": "owner"` |
| 5. Current User | `GET /auth/me` | Bearer Token | User ID & email (`401` without token) |
| 6. Refresh | `POST /auth/refresh` | Refresh Token | New token pair; old pair invalidated |
| 7. Logout | `POST /auth/logout` | Bearer + Refresh | Session revoked (`GET /auth/me` → `401`) |
| 8. Password Reset | `POST /auth/password-reset/*` | Reset Token | Old password fails; new password works |