# E-Commerce Coffee Shop Django Application

A fully-featured Django e-commerce application for buying and managing coffee products with user accounts, shopping cart, wishlist, reviews, and order management.

## 📋 Project Features

- **User Authentication**: User registration, login, and profile management
- **Product Catalog**: Browse coffee products by categories
- **Shopping Cart**: Add/remove items from cart with persistent storage
- **Wishlist**: Save favorite products for later
- **Product Reviews**: Users can leave ratings and reviews
- **Order Management**: Complete checkout and order history tracking
- **Admin Panel**: Django admin interface for managing products, orders, and users
- **Responsive Design**: Works on desktop and mobile devices

## 📁 Project Structure

```
E-commerce-coffee/
├── accounts/          # User authentication and profile management
├── products/          # Product catalog and details
├── cart/              # Shopping cart functionality
├── wishlist/          # Wishlist management
├── orders/            # Order processing and history
├── reviews/           # Product reviews and ratings
├── core/              # Main site pages (home, etc.)
├── config/            # Django configuration (settings, URLs, WSGI)
├── templates/         # HTML templates
├── static/            # CSS, JavaScript, and images
├── media/             # User-uploaded content
├── manage.py          # Django management script
├── requirements.txt   # Python dependencies
└── db.sqlite3         # SQLite database (development)
```

## 🔧 Prerequisites

- **Python 3.10+** - [Download Python](https://www.python.org/downloads/)
- **pip** - Usually comes with Python
- **Git** (optional) - For version control

## 📦 Installation & Setup

### Step 1: Navigate to the Project Directory

```bash
cd "path\to\E-commerce-coffee"
```

### Step 2: Create a Virtual Environment (Recommended)

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Create Environment Configuration File

A `.env` file has been created with the following default settings:

```
SECRET_KEY=django-insecure-dev-key-change-in-production-abc123xyz789
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000
```

**Note**: For production, change the `SECRET_KEY` and set `DEBUG=False`.

### Step 5: Run Migrations (Optional - Already Done)

If you need to create the database tables:

```bash
python manage.py migrate
```

### Step 6: Create a Superuser (Admin Account) (Optional - Already Done)

If you need to create another admin account:

```bash
python manage.py createsuperuser
```

**Existing Admin Account:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@example.com`

## 🚀 Running the Application

### Start the Development Server

```bash
python manage.py runserver
```

Or specify a custom port:

```bash
python manage.py runserver 0.0.0.0:8000
```

### Access the Application

Once the server is running, open your browser and visit:

- **Home Page**: [http://localhost:8000/](http://localhost:8000/)
- **Admin Panel**: [http://localhost:8000/admin/](http://localhost:8000/admin/)
  - Login with `admin` / `admin123`

## 📱 Main URL Routes

| Route | Purpose |
|-------|---------|
| `/` | Home page |
| `/products/` | Product list |
| `/products/<id>/` | Product detail |
| `/categories/` | Browse by categories |
| `/cart/` | Shopping cart |
| `/wishlist/` | Saved items |
| `/orders/checkout/` | Checkout page |
| `/orders/history/` | Order history |
| `/accounts/register/` | User registration |
| `/accounts/login/` | User login |
| `/accounts/profile/` | User profile |
| `/admin/` | Django admin panel |

## 🗄️ Database

- **Development**: SQLite (`db.sqlite3`) - No setup needed
- **Production**: PostgreSQL - Configure via `DATABASE_URL` in `.env`

### Using PostgreSQL

To switch to PostgreSQL, update your `.env` file:

```
DATABASE_URL=postgresql://username:password@localhost:5432/coffee_shop
```

Then run migrations:

```bash
python manage.py migrate
```

## 🔐 Environment Variables

Key environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `*` | Django secret key (change in production) |
| `DEBUG` | `True` | Debug mode (set to `False` in production) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed domains |
| `DATABASE_URL` | (empty) | PostgreSQL connection string |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:8000` | Trusted origins for CSRF |

## 📝 Useful Commands

### Create a New Superuser

```bash
python manage.py createsuperuser
```

### Reset the Database

```bash
python manage.py flush --no-input
python manage.py migrate
```

### Collect Static Files (Production)

```bash
python manage.py collectstatic --noinput
```

### Check Configuration

```bash
python manage.py check
```

### Access Django Shell

```bash
python manage.py shell
```

## 🐛 Troubleshooting

### Issue: Port 8000 Already in Use

Use a different port:

```bash
python manage.py runserver 8001
```

### Issue: "ModuleNotFoundError: No module named..."

Ensure virtual environment is activated and dependencies are installed:

```bash
pip install -r requirements.txt
```

### Issue: Database Errors

Reset and recreate the database:

```bash
python manage.py flush
python manage.py migrate
python manage.py createsuperuser
```

### Issue: Static Files Not Loading

Collect static files:

```bash
python manage.py collectstatic --noinput
```

## 🔒 Security Notes

⚠️ **Important for Production:**

1. Change the `SECRET_KEY` in `.env` to a random, secure value
2. Set `DEBUG=False`
3. Update `ALLOWED_HOSTS` with your domain(s)
4. Use a strong password for admin account
5. Set up proper email backend for password reset
6. Use HTTPS (set `SECURE_SSL_REDIRECT=True`)

## 📚 Technologies Used

- **Backend**: Django 5.1
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Frontend**: HTML, CSS, Bootstrap
- **Image Processing**: Pillow
- **Server**: Gunicorn (Production), Django Dev Server (Development)
- **Static Files**: WhiteNoise

## 🤝 Contributing

Feel free to make improvements to this project!

## 📄 License

This project is open source and available under the MIT License.

## ✅ Quick Start Checklist

- [x] Install Python 3.10+
- [x] Install dependencies: `pip install -r requirements.txt`
- [x] Create `.env` file (automatically created)
- [x] Run migrations: `python manage.py migrate`
- [x] Create superuser: Already done (admin/admin123)
- [x] Start server: `python manage.py runserver`
- [x] Visit [http://localhost:8000/](http://localhost:8000/)

## 📞 Support

If you encounter issues:

1. Check the Troubleshooting section above
2. Run `python manage.py check` to verify configuration
3. Check server logs in the terminal
4. Ensure all dependencies are installed

---

**Last Updated**: 2026-08-18

**Project Status**: ✅ Ready to Run
