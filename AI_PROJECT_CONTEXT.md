# BrewMart AI Project Context

> Living handoff for AI coding assistants and developers. This document records the repository as it is implemented, not as it is planned. Verify source code when behavior matters, then update this file when architecture, workflows, configuration, or known limitations change.

## 1. Project Snapshot

- **Name:** BrewMart
- **Purpose:** Django coffee e-commerce application with customer shopping, seller fulfillment, delivery operations, admin management, reviews, wishlists, wallets, and notifications.
- **Framework:** Django 5.1 (`Django>=5.1,<6.0`)
- **Runtime:** Python 3.10+
- **Default database:** SQLite in `db.sqlite3`
- **Optional database:** PostgreSQL when `DATABASE_URL` is non-empty
- **Frontend:** Django templates, shared styles in `static/css/`, uploaded content in `media/`
- **Static files:** WhiteNoise compressed manifest storage
- **WSGI entry point:** `config.wsgi.application`
- **Locale:** `en-us`; time zone: `Asia/Kathmandu`
- **Validation status:** `python manage.py check` passes as of 2026-09-27
- **Automated tests:** No test modules are currently visible; manual checks are required for feature changes.

## 2. AI Working Agreement

When modifying this project:

1. Read the owning model, service/workflow, view, URL, and template before editing. Treat implementation as authoritative over this document.
2. Preserve existing Django app boundaries and namespaced URL patterns. Prefer an existing service or helper over a new abstraction.
3. Treat `config/settings.py` as authoritative for environment behavior and `orders/workflow.py` as authoritative for normal order transitions.
4. Keep POST endpoints protected by authentication, authorization, and CSRF. Use transactions for order creation, stock changes, wallet transfers, and other multi-record mutations.
5. Never place secrets, real payment credentials, card numbers, CVV values, API tokens, or `.env` values in source, documentation, logs, or commits.
6. Keep demo payment behavior clearly labeled as demo behavior. Do not present it as a real provider integration.
7. After edits, run the narrowest relevant check, then at minimum run `python manage.py check`. For model changes, create and apply migrations; for workflows, exercise both allowed and rejected transitions.
8. Update this file only when a verified project fact changes. Add unresolved behavior to **Known Boundaries and Follow-up Work** instead of describing it as complete.

## 3. Setup and Daily Commands

Run commands from the directory containing `manage.py`.

### Windows setup

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The repository includes `.env.example`. Copy it to `.env` for local configuration, but keep `.env` private. The checked-in local database is suitable for development when `DATABASE_URL` is empty.

### Useful commands

```powershell
python manage.py check
python manage.py showmigrations
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py runserver 8001
python manage.py runserver_ssl
```

### Local entry points

- Store: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Admin dashboard: `http://127.0.0.1:8000/dashboard/`
- Optional local HTTPS: `https://localhost:8000/` using `runserver_ssl`

HTTPS development commands and certificate details are documented in [docs/RUN_PROJECT.md](docs/RUN_PROJECT.md).

## 4. Repository Map

| Area | Responsibility | Start here |
|---|---|---|
| `config` | Settings, root routing, WSGI | `config/settings.py`, `config/urls.py` |
| `core` | Home page, site context, sitemap/robots | `core/views.py`, `core/context_processors.py` |
| `accounts` | Registration, profile, roles, wallets | `accounts/models.py`, `accounts/services.py`, `accounts/views.py` |
| `products` | Categories and product catalog | `products/models.py`, `products/views.py` |
| `cart` | Session/user carts and cart mutations | `cart/models.py`, `cart/services.py`, `cart/views.py` |
| `wishlist` | User wishlists | `wishlist/models.py`, `wishlist/views.py` |
| `orders` | Checkout, payment simulators, order history, workflow | `orders/models.py`, `orders/views.py`, `orders/workflow.py` |
| `notifications` | In-app and optional email/WhatsApp delivery | `notifications/models.py`, `notifications/services.py` |
| `reviews` | Product ratings and comments | `reviews/models.py`, `reviews/views.py` |
| `dashboard` | Admin, seller, delivery operations and analytics | `dashboard/views.py`, `dashboard/decorators.py` |
| `templates` | Django HTML templates | `templates/base.html`, app subdirectories |
| `static` | Source CSS and other static assets | `static/css/` |
| `media` | Uploaded category and product images | `media/categories/`, `media/products/` |

## 5. URL Surface

Root routing is in `config/urls.py`.

| Prefix | App or feature |
|---|---|
| `/` | Core home |
| `/admin/` | Django admin |
| `/accounts/` | Account features and Django auth URLs |
| `/products/` | Product list, categories, details |
| `/cart/` | Cart detail, add, update, remove |
| `/wishlist/` | Wishlist operations |
| `/orders/` | Checkout, payment, history, status transitions |
| `/notifications/` | List and mark notifications read |
| `/reviews/` | Save/delete product reviews |
| `/dashboard/` | Admin, seller, and delivery dashboards |
| `/sitemap.xml` | Sitemap |
| `/robots.txt` | Robots response |

Important route shapes:

- Products: `/products/`, `/products/categories/`, `/products/category/<slug>/`, `/products/<slug>/`
- Accounts: `/accounts/login/`, `/accounts/register/`, `/accounts/profile/`, `/accounts/wallet/`
- Cart: `/cart/`, `/cart/add/<product_id>/`, `/cart/update/<item_id>/`, `/cart/remove/<item_id>/`
- Orders: `/orders/checkout/`, `/orders/payment/`, `/orders/success/<order_number>/`, `/orders/history/`, `/orders/<order_number>/transition/<new_status>/`
- Notifications: `/notifications/`, `/notifications/<notification_id>/read/`
- Dashboard operations are defined in `dashboard/urls.py`; do not infer them from the public route list.

## 6. Domain Model

### Users and wallets

- The project uses Django's built-in `auth.User` model.
- `accounts.Profile` is one-to-one with `User` and stores `BUYER`, `SELLER`, `DELIVERY`, or `ADMIN` role plus contact and shipping fields.
- `accounts.Wallet` is one-to-one with a user and has a non-negative decimal balance.
- `accounts.WalletTransfer` records sender, recipient, amount, note, unique `WAL-...` reference, and timestamp.
- Account signals create profiles/wallets for new accounts. Wallet transfers are implemented by `accounts.services.transfer_funds` inside an atomic transaction with deterministic wallet locking.

### Catalog and shopping

- `products.Category` has a unique name/slug and optional image.
- `products.Product` has category, name/slug, description, price, optional discount price, stock, image, optional seller, brand, unique SKU, featured/active flags, and timestamps.
- `Product.current_price` uses `discount_price` when present; otherwise it uses `price`.
- `cart.Cart` belongs to either one authenticated user or one anonymous session key.
- `cart.CartItem` stores quantity and has a unique `(cart, product)` relationship.
- `wishlist.Wishlist` is one-to-one with a user and has many-to-many products.
- `reviews.Review` allows one review per `(product, user)`.

### Orders

- `orders.Order` generates a unique `ORD-...` number.
- It snapshots buyer delivery details and order-item names/prices so historical orders do not depend on later product edits.
- An order may reference a buyer, protected seller, and delivery person.
- Payment fields include `payment_method`, `is_paid`, `payment_reference`, `transaction_hash`, and `transaction_signature`.
- Payment methods are `CARD`, `KHALTI`, `ESEWA`, and `COD`.
- Creating a successful order decreases stock and clears the current cart inside a transaction. If stock changed before creation, order creation is rejected and the cart remains available.

## 7. Roles and Order Workflow

Role constants live in `accounts.models.Profile.Role`. Dashboard access is implemented by `dashboard/decorators.py`; superusers bypass dashboard role checks, and admins may access seller/delivery dashboard views. Resource ownership still matters.

The normal workflow is enforced by `orders.workflow.TRANSITIONS`:

```text
PLACED -> ACCEPTED -> PREPARING -> READY_FOR_DELIVERY -> ASSIGNED
ASSIGNED -> PICKED_UP -> OUT_FOR_DELIVERY -> DELIVERED -> COMPLETED
```

Cancellation is allowed from `PLACED`, `ACCEPTED`, or `PREPARING` by the assigned seller. A seller can also assign a specific delivery rider directly from `PREPARING`; the normal open pool path is `READY_FOR_DELIVERY -> ASSIGNED` where a delivery user claims the job.

- Seller: accepts, prepares, marks ready, directly assigns, or cancels their own orders.
- Delivery user: claims available work, picks it up, marks it out for delivery, and marks it delivered after assignment.
- Buyer: confirms receipt, moving `DELIVERED -> COMPLETED`.
- Admin dashboard: has a separate order status form for operational support. Inspect that path before assuming it has the same restrictions or timestamp behavior as `transition_order`.

Successful workflow transitions create in-app notifications and queue optional external notifications with `transaction.on_commit`. Notification routing is controlled by `EXTERNAL_NOTIFY_ON`, `ADMIN_NOTIFY_ALL_ORDER_EVENTS`, and actor confirmation logic in `orders/workflow.py`.

## 8. Payments and Notifications

All payment gateways in `orders/payment_gateway.py` are local simulators. They do not contact banks, Khalti, eSewa, card networks, or payment providers.

Demo approval values:

| Method | Values |
|---|---|
| Card | `4111 1111 1111 1111`, expiry `12/30`, CVV `123` |
| Khalti-style | ID `9800000000`, MPIN `1111` |
| eSewa-style | ID `9800000001`, password `Nepal@123`, OTP `123456` |
| COD | No credentials; amount is collected on delivery |

Failed demo payments do not create an order. Successful orders receive a generated demo reference. The application canonicalizes transaction data and stores a SHA-256 hash plus an HMAC-SHA256 signature derived from `SECRET_KEY`; verification is in `orders.security.verify_transaction_signature`.

In-app notifications work independently of external channels. Email and WhatsApp are optional and are configured through `.env`. Supported WhatsApp providers are `twilio` and `meta`; phone numbers are normalized with `DEFAULT_PHONE_COUNTRY_CODE`. Provider failures are logged and should not roll back an order transition.

## 9. Configuration

`config/settings.py` loads `.env` with `python-dotenv`.

Important variables include:

```env
SECRET_KEY=use-a-long-random-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=
CSRF_TRUSTED_ORIGINS=http://localhost:8000
ORDER_NOTIFICATION_CHANNELS=
ADMIN_NOTIFY_ALL_ORDER_EVENTS=True
DEFAULT_PHONE_COUNTRY_CODE=+977
WHATSAPP_PROVIDER=twilio
GOOGLE_ANALYTICS_ID=
STORE_WHATSAPP_NUMBER=
```

SMTP, Twilio, and Meta credentials are documented in `.env.example`; never copy their values into this file. With `DEBUG=False`, settings enable secure cookies, HTTPS redirect according to `SECURE_SSL_REDIRECT`, proxy-aware HTTPS, content-type sniffing protection, same-origin referrer policy, and configurable HSTS.

## 10. Migrations and Documentation

- `accounts`: profiles, wallets/transfers, roles, admin role support
- `products`: catalog and seller relationship
- `cart`, `wishlist`, `reviews`, `notifications`: initial schemas
- `orders`: order schema, transaction proof, seller/delivery assignment, status normalization, payment fields, workflow timestamps
- `dashboard`: no domain models currently

Run `python manage.py migrate` after pulling schema changes. Do not edit an already-applied migration without a deliberate repair plan.

Documentation roles:

- [README.md](README.md): short project overview and feature demonstrations
- [docs/RUN_PROJECT.md](docs/RUN_PROJECT.md): Windows-first setup, HTTP/HTTPS, database, and deployment notes
- [docs/BrewMart_User_Guide.md](docs/BrewMart_User_Guide.md): user-facing usage guide
- [SETUP_GUIDE.md](SETUP_GUIDE.md): older broad setup guide; verify credentials and claims against source before relying on it
- `.env.example`: configuration reference without real secrets

## 11. Known Boundaries and Follow-up Work

- No automated test suite is currently visible. Add focused Django tests before making high-risk changes to checkout, permissions, stock, wallets, or workflow transitions.
- Demo payment gateways must be replaced with official provider integrations before production. A production design should create a pending order, verify the provider callback/server-side lookup, and only then finalize payment, stock, and status.
- Wallet balances are demonstration stored value. There is no real deposit, withdrawal, reconciliation, or external payment integration.
- The admin order-status form is intentionally a separate operational path and should be reviewed before expanding admin overrides or timestamp semantics.
- Media fallback serving is suitable for this project setup but should be replaced with a deliberate production media strategy.
- `README.md` and `SETUP_GUIDE.md` contain historical setup wording. Prefer `docs/RUN_PROJECT.md`, `.env.example`, and `config/settings.py` when they disagree.

## 12. Change Handoff Template

When another AI changes the project, it should leave a concise handoff in its response or task notes:

```text
Goal:
Changed files:
Behavior changed:
Data/migration impact:
Security/permission impact:
Validation run:
Known follow-up:
```

This document is context, not a substitute for reading the code that owns the behavior.