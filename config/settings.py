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
    "django.contrib.messages", "django.contrib.staticfiles", "django.contrib.sitemaps", "accounts", "products", "cart", "wishlist", "orders", "notifications", "reviews", "core", "dashboard",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages", "cart.context_processors.cart_summary", "wishlist.context_processors.wishlist_summary", "notifications.context_processors.notification_summary", "core.context_processors.site_settings"]}}]
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
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@brewmart.local")
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() == "true"
ORDER_NOTIFICATION_CHANNELS = os.getenv("ORDER_NOTIFICATION_CHANNELS", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "")

# Which WhatsApp backend to actually send through: "twilio" (above) or "meta"
# (Meta's own WhatsApp Cloud API -- no third party, no per-message cost on
# the free tier). Only one is used at a time; the other's settings are
# simply ignored.
WHATSAPP_PROVIDER = os.getenv("WHATSAPP_PROVIDER", "twilio").strip().lower()

# Meta WhatsApp Cloud API (used when WHATSAPP_PROVIDER=meta) ----------------
# From your Meta developer app's WhatsApp > API Setup page: META_WHATSAPP_TOKEN
# is the (temporary, or permanent once the app is live) access token, and
# META_WHATSAPP_PHONE_NUMBER_ID is the numeric ID shown there (not the phone
# number itself).
META_WHATSAPP_TOKEN = os.getenv("META_WHATSAPP_TOKEN", "")
META_WHATSAPP_PHONE_NUMBER_ID = os.getenv("META_WHATSAPP_PHONE_NUMBER_ID", "")
META_WHATSAPP_API_VERSION = os.getenv("META_WHATSAPP_API_VERSION", "v20.0")
# If True (default), every ADMIN-role account gets emailed/WhatsApp'd for every
# order event from checkout through delivery -- not just cancellations. Set to
# False in .env if that becomes too noisy and you'd rather only hear about
# cancellations, as before.
ADMIN_NOTIFY_ALL_ORDER_EVENTS = os.getenv("ADMIN_NOTIFY_ALL_ORDER_EVENTS", "True").lower() == "true"
# Prefixed onto phone numbers that don't already start with "+" before they're
# sent to Twilio, since WhatsApp requires E.164 format (e.g. +9779812345678)
# and most people just type a local 10-digit number at checkout or in their profile.
DEFAULT_PHONE_COUNTRY_CODE = os.getenv("DEFAULT_PHONE_COUNTRY_CODE", "+977")

# Optional Google Analytics 4 measurement ID (e.g. "G-XXXXXXXXXX"). Leave blank
# to ship no tracking code at all -- nothing renders in base.html until set.
GOOGLE_ANALYTICS_ID = os.getenv("GOOGLE_ANALYTICS_ID", "")

# Store's own WhatsApp number for the site-wide "Chat with us" button (local
# or +E.164 -- normalized the same way as DEFAULT_PHONE_COUNTRY_CODE above).
# Leave blank to hide the button entirely.
STORE_WHATSAPP_NUMBER = os.getenv("STORE_WHATSAPP_NUMBER", "")
if not DEBUG:
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() == "true"
    # Trust the X-Forwarded-Proto header from a reverse proxy/load balancer
    # (nginx, Render, Railway, Heroku, etc.) that terminates TLS in front of
    # this app. Without this, request.is_secure() always reports False behind
    # such a proxy, which breaks SECURE_SSL_REDIRECT (infinite redirect loop)
    # and secure-cookie behavior. Only trust this if the proxy is guaranteed
    # to set/overwrite the header itself -- never expose Django directly to
    # the internet with this on, since a client could otherwise spoof it.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    # HSTS ramp-up: start short (the 1-hour default below) so a misconfigured
    # certificate or a need to briefly fall back to HTTP doesn't lock visitors
    # out -- their browser would otherwise refuse to even attempt HTTP for as
    # long as the max-age says, with no way for you to undo that remotely.
    # Once HTTPS has been confirmed stable for a while, raise
    # SECURE_HSTS_SECONDS in .env (a year -- 31536000 -- is the common
    # production target) and only then consider INCLUDE_SUBDOMAINS/PRELOAD,
    # since PRELOAD submission to browsers is essentially irreversible.
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False").lower() == "true"
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "False").lower() == "true"
