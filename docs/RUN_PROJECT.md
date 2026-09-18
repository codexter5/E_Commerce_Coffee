# BrewMart: How to Run the Project

This guide is for starting the BrewMart Django e-commerce project after cloning it, reopening it later, or moving it to another machine.

## 1. Prerequisites

Install:

- Python 3.10 or newer
- Git, if you are cloning the project
- OpenSSL only if you need to generate a local HTTPS certificate
- PostgreSQL only if you choose PostgreSQL instead of the default SQLite database

Run all commands from the project directory, the folder that contains `manage.py`.

## 2. First-time setup on Windows

Open PowerShell and move to the project directory:

```powershell
cd "C:\path\to\E-commerce-coffee"
```

Create a virtual environment if `.venv` does not already exist:

```powershell
python -m venv .venv
```

Activate it:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `.env` does not exist, copy the example file and then edit it:

```powershell
Copy-Item .env.example .env
```

At minimum, check `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `DATABASE_URL` in `.env`. Keep `.env` private because it may contain passwords, tokens, or other credentials.

## 3. Prepare the database

The project uses SQLite by default when `DATABASE_URL` is empty. The included `db.sqlite3` is suitable for local development.

Apply migrations:

```powershell
python manage.py migrate
```

Create an administrator account when needed:

```powershell
python manage.py createsuperuser
```

Optional checks:

```powershell
python manage.py check
python manage.py showmigrations
```

## 4. Run with normal HTTP

Make sure the virtual environment is active, then run:

```powershell
python manage.py runserver
```

Open:

- Store: <http://127.0.0.1:8000/>
- Admin: <http://127.0.0.1:8000/admin/>

Stop the server with `Ctrl+C`.

To use another port:

```powershell
python manage.py runserver 127.0.0.1:8001
```

## 5. Run with local HTTPS

This project includes a custom HTTPS development command and certificate files under `certs/`.

### Start HTTPS

```powershell
python manage.py runserver_ssl
```

Open:

- Store: <https://localhost:8000/>
- Admin: <https://localhost:8000/admin/>

The local certificate is self-signed, so the browser will show a certificate warning. That is expected for local testing. Continue only when you are sure the address is `localhost` or `127.0.0.1`.

You can choose another HTTPS port:

```powershell
python manage.py runserver_ssl 127.0.0.1:8443
```

### Generate or renew the local certificate

The existing files are:

```text
certs/dev-cert.pem
certs/dev-key.pem
```

If they are missing or expired, generate them with:

```powershell
python manage.py generate_dev_cert
```

To replace an existing certificate:

```powershell
python manage.py generate_dev_cert --force
```

The certificate command requires `openssl` on `PATH`. On Windows, use OpenSSL from Git Bash, WSL, or a Windows OpenSSL installation. After generating custom files, pass them explicitly:

```powershell
python manage.py runserver_ssl --cert "C:\path\to\certificate.pem" --key "C:\path\to\private-key.pem"
```

Do not use a self-signed development certificate for a public website.

## 6. Choosing SQLite or PostgreSQL

### SQLite for local development

Leave `DATABASE_URL` empty or remove it from `.env`:

```env
DATABASE_URL=
```

Then run:

```powershell
python manage.py migrate
```

### PostgreSQL

Create a PostgreSQL database and set its connection string in `.env`:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/coffee_shop
```

Then run:

```powershell
python manage.py migrate
```

The `psycopg` dependency is already listed in `requirements.txt`.

## 7. Important environment settings

Typical local settings:

```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://localhost:8000,http://127.0.0.1:8000,https://127.0.0.1:8000
```

For production:

```env
DEBUG=False
SECRET_KEY=use-a-long-random-secret
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
SECURE_SSL_REDIRECT=True
```

When `DEBUG=False`, Django enables secure session and CSRF cookies and redirects HTTP requests to HTTPS. The application expects a trusted reverse proxy or hosting platform to terminate TLS and send `X-Forwarded-Proto: https` to Django.

## 8. Production HTTPS overview

Do not expose `python manage.py runserver` or `runserver_ssl` to the public internet. For production:

1. Deploy Django behind a hosting platform or reverse proxy such as Nginx.
2. Obtain a trusted certificate from your hosting provider or a certificate authority such as Let's Encrypt.
3. Configure the proxy to redirect HTTP to HTTPS and forward HTTPS requests to the Django application.
4. Set `DEBUG=False`, the real host names, and HTTPS CSRF origins in `.env`.
5. Run migrations and collect static files:

```powershell
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

6. Keep database passwords, email passwords, API tokens, and the production `SECRET_KEY` outside Git.

The included Gunicorn dependency is intended for Linux-based production hosting. On Windows, use the process manager recommended by your hosting provider rather than relying on the Django development server.

## 9. Useful application commands

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py check
python manage.py check --deploy
```

Use `makemigrations` only after changing models. Never delete production migrations or reset a production database as a troubleshooting shortcut.

## 10. Troubleshooting

### The browser says the site cannot be reached

Confirm the server is still running in the terminal and use the correct scheme:

- HTTP server: `http://127.0.0.1:8000/`
- HTTPS server: `https://localhost:8000/`

### `Certificate not found`

Run:

```powershell
python manage.py generate_dev_cert
```

If OpenSSL is unavailable, install it or provide existing PEM files with `--cert` and `--key`.

### `DisallowedHost`

Add the hostname you are using to `ALLOWED_HOSTS` in `.env`, then restart Django. For local development, use:

```env
ALLOWED_HOSTS=localhost,127.0.0.1
```

### CSRF verification failed

Add the exact HTTP or HTTPS origin, including its port, to `CSRF_TRUSTED_ORIGINS` in `.env`, then restart the server.

### Database or missing-module errors

Activate the virtual environment and reinstall dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
```

### Static files are missing

For development, confirm `DEBUG=True`. For a production-like check, run:

```powershell
python manage.py collectstatic --noinput
```

## 11. Quick restart checklist

For future sessions, the usual sequence is:

```powershell
cd "C:\path\to\E-commerce-coffee"
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver_ssl
```

Then visit <https://localhost:8000/>.
