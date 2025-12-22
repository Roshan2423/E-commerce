# Django E-Commerce Platform with MongoDB

A comprehensive e-commerce platform built with Django and MongoDB, featuring a powerful admin panel with vertical navigation for managing products, orders, and analytics.

## 🚀 Features

### Backend (Django + MongoDB)
- **Modern Admin Panel** with vertical sidebar navigation
- **Product Management**: Full CRUD operations with categories, variants, and images
- **Order Management**: Complete order processing workflow
- **User Authentication**: Custom user model with email-based login
- **Analytics Dashboard**: Sales reports, customer insights, and business metrics
- **Security Features**: CSRF protection, secure headers, input validation
- **MongoDB Integration**: Using Djongo for seamless Django-MongoDB compatibility

### Admin Panel Sections
- 📊 **Dashboard**: Analytics, recent orders, low stock alerts
- 📦 **Products**: Product catalog management with categories
- 🛒 **Orders**: Order processing and tracking
- 📈 **Reports**: Sales, product, and customer analytics

### Frontend (Sample)
- Responsive Bootstrap-based design
- Sample product showcase
- Admin panel access links
- Modern UI with animations

## 🛠️ Technology Stack

- **Backend**: Django 4.2.7, Python 3.8+
- **Database**: MongoDB with Djongo ORM
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Authentication**: Django Allauth
- **Security**: Multiple layers of security implementation

## 📁 Project Structure

```
ecommerce-platform/
├── backend/
│   ├── ecommerce/          # Django project settings
│   ├── accounts/           # User management
│   ├── products/           # Product catalog
│   ├── orders/             # Order processing
│   ├── dashboard/          # Admin dashboard
│   ├── reports/            # Analytics & reports
│   ├── templates/          # HTML templates
│   ├── static/             # CSS, JS, images
│   └── manage.py
├── frontend/
│   └── index.html          # Sample frontend
├── setup_project.py        # Automated setup script
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- MongoDB installed and running
- pip (Python package installer)

### Installation

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd ecommerce-platform
   python setup_project.py
   ```

2. **Manual Setup (Alternative)**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   cd backend
   pip install -r requirements.txt
   
   # Setup environment
   cp .env.example .env
   # Edit .env with your settings
   
   # Run migrations
   python manage.py makemigrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   
   # Start server
   python manage.py runserver
   ```

### 🔧 Configuration

Edit `backend/.env` file:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB Settings
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_NAME=ecommerce_db
MONGODB_USER=
MONGODB_PASSWORD=

# Email Settings (for user verification)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## 🎯 Usage

### Admin Panel Access
- **Custom Dashboard**: `http://localhost:8000/dashboard/`
- **Django Admin**: `http://localhost:8000/admin/`
- **Sample Frontend**: `../frontend/index.html`

### Admin Panel Features

#### 📊 Dashboard
- Real-time analytics and KPIs
- Recent orders overview
- Low stock alerts
- Top-selling products
- Sales charts and graphs

#### 📦 Product Management
- Add/edit/delete products
- Category management
- Product variants and images
- Inventory tracking
- SEO optimization fields

#### 🛒 Order Management
- Order status tracking
- Payment status updates
- Shipping management
- Order cancellation
- Customer communication

#### 📈 Reports & Analytics
- Sales reports with date filtering
- Product performance metrics
- Customer acquisition data
- Revenue analytics

## 🔒 Security Features

- CSRF protection enabled
- Secure headers configuration
- Input validation and sanitization
- User authentication and authorization
- Password complexity requirements
- Secure session management
- XSS protection

## 📊 Database Models

### Key Models:
- **User**: Custom user model with email authentication
- **Product**: Complete product information with variants
- **Category**: Product categorization
- **Order**: Order processing and tracking
- **OrderItem**: Individual order line items
- **Address**: User shipping/billing addresses

## 🔄 API Structure

The platform is designed to be easily extended with REST API capabilities:
- All views use class-based views for consistency
- Models are well-structured for API serialization
- Authentication system ready for API token integration

## 🚀 Deployment

### Production Checklist:
1. Set `DEBUG=False` in production
2. Configure proper database credentials
3. Set up email backend for notifications
4. Configure static files serving
5. Set up SSL certificates
6. Configure proper logging

### Environment Variables:
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
MONGODB_HOST=your-mongo-host
SECURE_SSL_REDIRECT=True
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📋 TODO / Future Enhancements

- [ ] REST API implementation
- [ ] Shopping cart functionality
- [ ] Payment gateway integration (Stripe/PayPal)
- [ ] Email notifications
- [ ] Product reviews and ratings
- [ ] Inventory management
- [ ] Multi-vendor support
- [ ] Advanced search and filtering
- [ ] Wishlist functionality
- [ ] Mobile app support

## 🐛 Troubleshooting

### Common Issues:

1. **MongoDB Connection Error**
   ```
   Ensure MongoDB is running: mongod
   Check connection settings in .env file
   ```

2. **Migration Errors**
   ```
   python manage.py makemigrations --empty accounts
   python manage.py migrate
   ```

3. **Static Files Not Loading**
   ```
   python manage.py collectstatic
   Check STATIC_ROOT and STATIC_URL settings
   ```

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review Django and MongoDB documentation

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Built with ❤️ using Django and MongoDB**