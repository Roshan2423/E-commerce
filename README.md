# OVN Store - E-Commerce Platform

A modern e-commerce platform built with Django. Single server setup serving both the customer-facing store and admin panel.

## Features

### Customer Store
- Modern, responsive design with glassmorphism effects
- Product catalog with categories
- Shopping cart functionality
- User authentication (Email & Google OAuth)
- Product search and filtering

### Admin Panel
- Modern dashboard with analytics
- Product management (CRUD)
- Order management and tracking
- Customer management
- Sales reports and insights

## Tech Stack

- **Backend**: Django 4.2, Python 3.8+
- **Database**: SQLite (default) or PostgreSQL
- **Frontend**: Vanilla JavaScript, Modern CSS
- **Authentication**: Django Sessions, Google OAuth

## Project Structure

```
e-commerce/
├── backend/
│   ├── ecommerce/          # Django settings
│   ├── accounts/           # User authentication
│   ├── products/           # Product catalog
│   ├── orders/             # Order processing
│   ├── dashboard/          # Admin dashboard
│   ├── reports/            # Analytics
│   ├── frontend/           # Frontend app
│   ├── templates/          # HTML templates
│   │   ├── admin/          # Admin panel templates
│   │   └── frontend/       # Store templates
│   ├── static/
│   │   ├── css/            # Admin CSS
│   │   ├── js/             # Admin JS
│   │   └── frontend/       # Store CSS/JS
│   └── manage.py
├── start.py                # Single startup script
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# 1. Clone and enter directory
cd e-commerce

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Run migrations
cd backend
python manage.py migrate

# 4. Create admin user
python manage.py createsuperuser

# 5. Start the server
cd ..
python start.py
```

### Access Points

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000/ | Customer Store |
| http://127.0.0.1:8000/login | Login Page |
| http://127.0.0.1:8000/dashboard/ | Admin Dashboard |
| http://127.0.0.1:8000/products/ | Product Management |
| http://127.0.0.1:8000/orders/ | Order Management |

## Configuration

Create `backend/.env` file (optional):

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Google OAuth Setup (Optional)

To enable Google Sign-In:

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create or select your OAuth 2.0 Client ID
3. Add these **Authorized JavaScript origins**:
   - `http://localhost:8000`
   - `http://127.0.0.1:8000`
4. Add these **Authorized redirect URIs**:
   - `http://localhost:8000/login`
   - `http://127.0.0.1:8000/login`
5. Save and wait 5 minutes for changes to propagate

## Authentication Flow

1. User visits `/dashboard/` or any admin page
2. If not logged in, redirected to `/login`
3. User logs in via email/password or Google OAuth
4. Admin users automatically redirected to dashboard
5. Regular users stay on the store

## Deployment

### Single Server Benefits
- No CORS configuration needed
- Same-origin cookies work automatically
- One process to manage
- Simpler deployment
- Lower hosting cost

### Production Checklist
1. Set `DEBUG=False`
2. Set a strong `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Set up SSL (HTTPS)
5. Run `python manage.py collectstatic`
6. Use a production server (Gunicorn + Nginx)

### Deploy to Railway/Render

```bash
# Just push to git - CI/CD handles the rest
git push origin main
```

## Development

### Running the Server
```bash
python start.py
# or
cd backend && python manage.py runserver
```

### Creating New Admin User
```bash
cd backend
python manage.py createsuperuser
```

### Collecting Static Files
```bash
cd backend
python manage.py collectstatic
```

## Troubleshooting

### Static Files Not Loading
```bash
cd backend
python manage.py collectstatic --noinput
```

### Migration Issues
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

## License

MIT License - feel free to use for your projects.

---
**Built with Django**
