import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-development-key-change-me")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")]
CSRF_TRUSTED_ORIGINS = [u.strip() for u in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if u.strip()]

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles", "accounts", "products", "cart", "wishlist", "orders", "notifications", "reviews", "core",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages", "cart.context_processors.cart_summary", "wishlist.context_processors.wishlist_summary", "notifications.context_processors.notification_summary"]}}]
WSGI_APPLICATION = "config.wsgi.application"

db_url = os.getenv("DATABASE_URL", "")
if db_url:
    p = urlparse(db_url)
    DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": p.path.lstrip("/"), "USER": p.username, "PASSWORD": p.password, "HOST": p.hostname, "PORT": p.port or 5432, "CONN_MAX_AGE": 600}}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"}, {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"}, {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"}, {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"}]
LANGUAGE_CODE, TIME_ZONE, USE_I18N, USE_TZ = "en-us", "Asia/Kathmandu", True, True
STATIC_URL, STATIC_ROOT, STATICFILES_DIRS = "/static/", BASE_DIR / "staticfiles", [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL, MEDIA_ROOT = "/media/", BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL, LOGIN_URL = "core:home", "core:home", "login"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
if not DEBUG:
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() == "true"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    SECURE_HSTS_SECONDS, SECURE_HSTS_INCLUDE_SUBDOMAINS, SECURE_HSTS_PRELOAD = 31536000, True, True
