# GarageBuddy-project
Garage Buddy is a web-based garage management system developed to address these operational challenges head-on. Built using Django as the backend framework and MongoDB as the database, the application provides a admin-only portal that digitalize every aspect of a two-wheeler garage's workflow from the moment a customer registers their vehicle.



# 🏍️ Garage Buddy — Two-Wheeler Garage Management System
## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Running the Server](#running-the-server)
  - [Setting Up Celery (Reminders)](#setting-up-celery-reminders)
- [Project Structure](#-project-structure)
- [Database Collections](#-database-collections)
- [Workflow](#-workflow)
- [API / URL Routes](#-url-routes)
- [Screenshots](#-screenshots)
- [Build Phases](#-build-phases)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 About the Project

**Garage Buddy** is a full-featured, admin-only web application for two-wheeler repair and service garages. It replaces manual paper registers and informal tracking with a centralised digital system — covering everything from customer registration to PDF invoice generation and automated 3-month service reminders.

> **Admin-only access** — No customer-facing portal. All operations are performed by the garage owner/admin through a single secure login.

---

## ✨ Features

| Module | Description |
|---|---|
|  **Admin Authentication** | Secure login with Django session auth. All views protected by `@login_required`. |
|  **Customer Management** | Add, edit, view, and delete customer profiles. |
|  **Vehicle Management** | Register two-wheelers linked to customers (make, model, reg. number). |
|  **Service Job Tracking** | Create job cards, assign repair types, track status: `Pending → In Progress → Done`. |
|  **Billing & Invoicing** | Auto-calculate bills (parts + labour + tax), mark payment status, download PDF invoices. |
|  **Service History** | Complete per-vehicle and per-customer job history log. |
|  **Automated Reminders** | Celery periodic task sends SMS/email reminders every 3 months after last service. |
|  **Admin Dashboard** | Real-time overview — active jobs, revenue, pending bills, due reminders + charts. |

---

## 🛠️ Tech Stack

```
Backend      →  Django 4.x (Python 3.10+)
Database     →  MongoDB 6.x via Djongo ORM
Frontend     →  HTML5, CSS3, JavaScript, Chart.js
Task Queue   →  Celery 5.x + Redis
PDF Engine   →  WeasyPrint
Auth         →  Django built-in (session-based)
Deployment   →  Gunicorn + Nginx / Railway / Render
Cloud DB     →  MongoDB Atlas
```

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

- Python 3.10+
- MongoDB (local) or a [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) account
- Redis (for Celery)
- pip & virtualenv

---

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/your-username/garage-buddy.git
cd garage-buddy
```

**2. Create and activate a virtual environment**

```bash
python -m venv env

# Windows
env\Scripts\activate

# macOS / Linux
source env/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Apply migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

**5. Create the admin superuser**

```bash
python manage.py createsuperuser
```

---

### Environment Variables

Create a `.env` file in the root directory:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB
MONGO_DB_NAME=garagebuddy
MONGO_URI=mongodb://localhost:27017/

# Email (for reminders)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

---

Running the Server

```bash
python manage.py runserver
```

Visit: [http://127.0.0.1:8000/admin-login/](http://127.0.0.1:8000/admin-login/)

---

### Setting Up Celery (Reminders)

Open a second terminal and start Redis:

```bash
redis-server
```

Start the Celery worker:

```bash
celery -A garagems worker --loglevel=info
```

Start the Celery beat scheduler (for periodic tasks):

```bash
celery -A garagems beat --loglevel=info
```

> The reminder task runs automatically every 3 months for customers whose last service was 90 days ago.

---

## 📁 Project Structure

```
garage-buddy/
│
├── garagems/                   # Django project root
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py               # Celery app config
│   └── wsgi.py
│
├── garage/                     # Main Django app
│   ├── models.py               # Customer, Vehicle, ServiceJob, Bill, ServiceHistory
│   ├── views.py                # All CRUD and dashboard views
│   ├── urls.py                 # App-level URL patterns
│   ├── forms.py                # Django model forms
│   ├── tasks.py                # Celery reminder task
│   └── admin.py                # Django admin registration
│
├── templates/                  # HTML templates
│   ├── base.html               # Base layout with nav
│   ├── login.html              # Admin login page
│   ├── dashboard.html          # Dashboard with charts
│   ├── customers/              # Customer list, add, edit
│   ├── vehicles/               # Vehicle list, add, edit
│   ├── jobs/                   # Job card list, create, update
│   ├── billing/                # Bill generator, invoice
│   └── history/                # Service history view
│
├── static/                     # CSS, JS, images
│   ├── css/
│   ├── js/
│   └── img/
│
├── requirements.txt
├── .env.example
├── .gitignore
├── manage.py
└── README.md
```

---

## 🗄️ Database Collections

| Collection | Fields |
|---|---|
| `customers` | `id`, `name`, `phone`, `email`, `address`, `created_at` |
| `vehicles` | `id`, `customer_id`, `make`, `model`, `year`, `reg_no` |
| `service_jobs` | `id`, `vehicle_id`, `type`, `description`, `parts`, `status`, `created_at`, `updated_at` |
| `bills` | `id`, `job_id`, `parts_cost`, `labour_cost`, `tax`, `total`, `is_paid`, `created_at` |
| `service_history` | `id`, `vehicle_id`, `customer_id`, `job_ref`, `bill_ref`, `completed_at` |

---

## 🔄 Workflow

```
Admin Login
    │
    ├── Register Customer
    │       └── Add Vehicle (linked to customer)
    │
    ├── Create Service Job (Pending)
    │       └── Update Status → In Progress → Done
    │
    ├── Generate Bill (auto-calculated)
    │       ├── Mark as Paid / Unpaid
    │       └── Download PDF Invoice
    │
    ├── Service History (auto-logged on job completion)
    │
    ├── Automated Reminder (Celery — every 3 months)
    │       └── SMS / Email sent to customer
    │
    └── Dashboard (live stats + charts)
```

---

URL Routes

| URL | View | Description |
|---|---|---|
| `/admin-login/` | `LoginView` | Admin login page |
| `/dashboard/` | `DashboardView` | Main dashboard |
| `/customers/` | `CustomerListView` | List all customers |
| `/customers/add/` | `CustomerCreateView` | Add new customer |
| `/customers/<id>/edit/` | `CustomerUpdateView` | Edit customer |
| `/vehicles/` | `VehicleListView` | List all vehicles |
| `/vehicles/add/` | `VehicleCreateView` | Add new vehicle |
| `/jobs/` | `JobListView` | List all service jobs |
| `/jobs/create/` | `JobCreateView` | Create a job card |
| `/jobs/<id>/status/` | `JobStatusUpdateView` | Update job status |
| `/billing/` | `BillListView` | List all bills |
| `/billing/<job_id>/generate/` | `BillCreateView` | Generate a bill |
| `/billing/<id>/invoice/` | `InvoicePDFView` | Download PDF invoice |
| `/history/` | `ServiceHistoryView` | View service history |

---

## 📸 Screenshots



Build Phases

| Phase | Focus | Status |
|---|---|---|
| 1 | Project setup & MongoDB connection | ✅ Done |
| 2 | Admin authentication | ✅ Done |
| 3 | Customer & vehicle management | ✅ Done |
| 4 | Service job tracking | ✅ Done |
| 5 | Billing & PDF invoicing | ✅ Done |
| 6 | Celery automated reminders | 🔄 In Progress |
| 7 | Admin dashboard & charts | 🔄 In Progress |
| 8 | Testing & deployment | ⏳ Pending |

Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

Please make sure your code follows PEP 8 and includes relevant tests.


**Garage Buddy** — Smarter garage management for modern two-wheeler repair shops.

Recording of Project Link - https://drive.google.com/file/d/1m_SkxaVQMk6v_u_VvJkpRUkUbNSEkXWS/view?usp=sharing
