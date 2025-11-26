# Backend & Middleware Specification

## 1. Directory Structure
/src
  /config       # DB connections, Env variables
  /controllers  # Request logic (Auth, Product)
  /middleware   # Interceptors
  /models       # Database Schemas
  /routes       # Express route definitions
  /utils        # Helper functions (Logger, AppError)

## 2. Database Schema (PostgreSQL)

### Table: Users
| Column       | Type         | Constraints |
|--------------|--------------|-------------|
| id           | UUID         | PK          |
| email        | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash| VARCHAR      | NOT NULL    |
| role         | ENUM         | ('user', 'admin') |
| created_at   | TIMESTAMP    | DEFAULT NOW() |

### Table: Products
| Column       | Type         | Constraints |
|--------------|--------------|-------------|
| id           | UUID         | PK          |
| name         | VARCHAR(255) | NOT NULL    |
| price        | DECIMAL      | NOT NULL    |
| stock        | INT          | DEFAULT 0   |

## 3. Middleware Logic

### `authMiddleware.js`
1.  Extract `Authorization` header (Bearer Token).
2.  Verify JWT using the `JWT_SECRET`.
3.  If valid, attach `user` object to `req.user` and call `next()`.
4.  If invalid, return `401 Unauthorized`.

### `errorMiddleware.js`
* Catches async errors.
* Formats response standard: `{ success: false, message: "Error details", stack: "..." }` (Stack hidden in production).