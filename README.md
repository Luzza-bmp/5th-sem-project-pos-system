# 5th-sem-project-pos-system
# Pasaley
### Multi-Tenant Cloud Point-of-Sale System with AI-Assisted Inventory Restocking

Pasaley is a cloud-based Point-of-Sale (POS) system designed to help businesses manage sales, products, inventory, invoices, and payments from a centralized platform.

The system follows a **multi-tenant architecture**, allowing multiple independent stores to use the same application while keeping their data isolated and secure.

It also aims to integrate AI-assisted inventory analysis to help store owners make better restocking decisions based on historical sales and stock information.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Objectives](#objectives)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Database Design](#database-design)
- [Database Security](#database-security)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Database Setup](#database-setup)
- [Environment Variables](#environment-variables)
- [Contributors](#contributors)

---

## Project Overview

Traditional small businesses often manage their sales and inventory manually or use disconnected systems. This can lead to inaccurate stock records, inefficient billing, difficulty tracking sales, and poor restocking decisions.

Pasaley aims to solve these problems by providing a centralized POS platform with inventory management and AI-assisted restocking capabilities.

The system is designed around three important principles:

1. **Multi-tenancy:** Multiple stores can operate independently on the same platform.
2. **Security:** Store data must remain isolated, with access controlled by user roles and database-level security.
3. **Intelligence:** Historical sales and inventory data can be used to generate useful restocking recommendations.

## Objectives

- Develop a cloud-based POS system for multiple stores.
- Provide secure user authentication and role-based access control.
- Simplify product, inventory, sales, and payment management.
- Maintain accurate stock records and transaction history.
- Generate invoices and sales reports.
- Implement AI-assisted inventory restocking recommendations.
- Ensure secure data isolation between different stores.

## Key Features

### 1. User Authentication and Authorization
- User registration and login.
- Secure password storage.
- JWT-based authentication.
- Role-based access control.
- Two-factor authentication.
- Protected API endpoints.

### 2. Multi-Tenant Store Management
- Register and manage stores.
- Manage store owners and employees.
- Invite employees to stores.
- Assign roles and permissions.
- Keep each store's data isolated.

### 3. Product and Inventory Management
- Add, update, and manage products.
- Track available stock.
- Record stock movements.
- Manage restocking batches.
- Monitor inventory levels.
- Generate low-stock alerts.

### 4. Point-of-Sale Management
- Search and select products.
- Create sales transactions.
- Calculate totals and discounts.
- Generate invoices and receipts.
- Record customer payments.
- Maintain sales history.

### 5. AI-Assisted Inventory Restocking
- Analyze historical sales data.
- Identify frequently sold products.
- Estimate future inventory requirements.
- Recommend restocking quantities.
- Help store owners make informed inventory decisions.

### 6. Reports and Analytics
- View sales summaries.
- Monitor inventory levels.
- Track payments and transactions.
- Analyze product performance.

*Features are planned for implementation unless explicitly marked as completed in the project status section.*

---

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | React |
| Database | PostgreSQL |
| Database Platform | Supabase |
| ORM | SQLAlchemy |
| Database Migrations | Alembic |
| Data Validation | Pydantic |
| Authentication | JWT |
| Database Security | PostgreSQL Row-Level Security (RLS) |
| Version Control | Git and GitHub |

---

### Architecture Explanation

- **React:** Provides the user interface.
- **FastAPI:** Handles API requests and application logic.
- **Authentication:** Verifies users and controls access to protected endpoints.
- **SQLAlchemy:** Handles database interactions.
- **PostgreSQL:** Stores application data.
- **RLS:** Enforces row-level access restrictions inside the database.
- **AI Restocking Service:** Analyzes inventory and sales information to generate recommendations.

---

## Database Design

The initial database schema contains 11 application tables.

| Table | Purpose |
|---|---|
| `users` | Stores user account information |
| `stores` | Stores registered shop information |
| `members` | Connects users with stores and their roles |
| `invites` | Manages store invitations |
| `products` | Stores product information |
| `invoices` | Stores sales invoices |
| `items` | Stores individual invoice items |
| `payments` | Stores payment records |
| `stock_movements` | Tracks inventory changes |
| `restock_batches` | Stores restocking batch information |
| `restock_lines` | Stores individual items in restocking batches |

The schema is managed using SQLAlchemy models and Alembic migrations.

### Database Migrations

Alembic is used to maintain database schema changes in version control.

This allows every developer to reproduce the same database structure without manually creating tables.

To apply all available migrations:

```bash
alembic upgrade head
```

---

## Database Security

Database security is a core part of Pasaley because multiple independent stores share the same database infrastructure.

### 1. PostgreSQL Roles

Two database roles have been created to separate responsibilities:

| Role | Responsibility |
|---|---|
| `pasaley_app` | Handles normal application database operations |
| `pasaley_provisioner` | Provides restricted permissions for initial store provisioning |

This follows the principle of **Least Privilege**, meaning each role receives only the permissions it needs.

### 2. Row-Level Security (RLS)

RLS is enabled on all 11 application tables.

It ensures that users can only access records they are authorized to access.

For example:
- A store owner can access their own store's authorized data.
- A manager can perform permitted management operations.
- An active store member can access permitted store information.
- Users cannot access another store's private records simply by changing an API request.

### 3. Database Security Functions

The security migration introduces functions such as:

- `current_app_user_id()` — identifies the authenticated application user within the database transaction.
- `has_store_role()` — checks whether a user has an allowed role in a store.
- `is_active_store_member()` — checks active store membership.
- `provision_initial_store()` — handles initial store provisioning.
- `rls_auto_enable()` — supports automatic RLS enablement on newly created public tables.

The backend must verify the user's JWT before setting the authenticated user ID in the database transaction. The user ID must never be trusted directly from frontend input.

### 4. Security Migration

The database security migration is:

`6917bb725011_add_database_security_and_rls_policies.py`

It adds the database roles' required privileges, security functions, RLS policies, and automatic RLS trigger.

---

## Project Structure

The repository is organized into separate frontend and backend components.

```text
5th-sem-project-pos-system/
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── ...
│   │
│   ├── database/
│   │   └── bootstrap_roles.sql
│   │
│   ├── migrations/
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env
│
├── frontend/
│   └── ...
│
├── docs/
│   └── ...
│
├── .gitignore
└── README.md
```

*The structure will expand as additional modules are implemented.*

---

## Getting Started

Follow these instructions to set up your local development environment.

### Prerequisites

Make sure you have installed:

- Python 3.12
- Git
- Node.js and npm (for frontend development)
- A Supabase account
- A code editor such as Visual Studio Code

### 1. Clone the Repository

```bash
git clone https://github.com/Luzza-bmp/5th-sem-project-pos-system.git
```

Navigate into the project:

```bash
cd 5th-sem-project-pos-system
```

Switch to the database development branch if you need the latest database migrations:

```bash
git checkout database
```

### 2. Set Up the Backend

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure the Database

Create your own Supabase development project.

Do not use another developer's database credentials. Each developer should use an independent development database.

Follow the [Database Setup Guide](docs/DATABASE_SETUP.md) if it is available in the repository.

---

## Database Setup

The database uses two connection URLs.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Application runtime connection using `pasaley_app` |
| `MIGRATION_DATABASE_URL` | Migration connection with the privileges required to apply schema and security migrations |

Apply migrations:

```bash
alembic upgrade head
```

Verify the current migration:

```sql
SELECT version_num FROM alembic_version;
```

The latest database security migration revision is:

```text
6917bb725011
```

**Important:** The migration connection requires sufficient privileges for the operations in the migrations. Do not use the application runtime credentials to perform database migrations.

---

## Environment Variables

Create a `.env` file inside the `backend/` directory.

Example:

```env
DATABASE_URL=postgresql://pasaley_app:YOUR_APP_PASSWORD@YOUR_HOST:5432/postgres

MIGRATION_DATABASE_URL=postgresql://postgres:YOUR_DB_PASSWORD@YOUR_HOST:5432/postgres
```

Replace the placeholders with your own Supabase connection details.

## Contributors

This project is being developed collaboratively as an academic team project at Kathmandu University.

All team members contribute to the development of different modules, including database management, backend development, frontend development, security, and AI-assisted inventory features.

---

## License

This project is developed for academic purposes as part of a Kathmandu University semester project.

