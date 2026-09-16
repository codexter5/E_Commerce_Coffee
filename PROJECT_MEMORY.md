# BrewMart Project Memory

This file is a compact handoff document for another AI model or developer. It describes the current repository as implemented, not an aspirational design. Re-check the source files when making changes because this document can become stale.

## 1. Project Identity

- Project: BrewMart, a coffee e-commerce web application.
- Framework: Django 5.1 (`Django>=5.1,<6.0`).
- Language/runtime: Python 3.10+.
- Primary local database: SQLite at `db.sqlite3`.
- Production database option: PostgreSQL through `DATABASE_URL` and `psycopg`.
- Time zone: `Asia/Kathmandu`; language: `en-us`.
- Frontend: Django templates, CSS in `static/css/site.css`, uploaded media in `media/`.
- Static serving: WhiteNoise with compressed manifest storage.
- Deployment entry point: `config.wsgi.application`.

## 2. How To Run

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Useful commands:

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver 8001
```

Main local URLs:

- Site home: `http://localhost:8000/`
- Django admin: `http://localhost:8000/admin/`
- Admin dashboard: `http://localhost:8000/dashboard/`

The repository may contain a local `.env`; never copy its secret values into documentation or expose them in commits. `config/settings.py` loads `.env` automatically.

## 3. Dependencies

- Django 5.1
- `psycopg[binary]` for PostgreSQL
- Pillow for image fields
- python-dotenv for environment configuration
- Gunicorn for production WSGI serving
- WhiteNoise for static files
- ReportLab for PDF-related functionality

## 4. Django Applications

| App | Responsibility | Important files |
|---|---|---|
| `config` | Settings, root URL routing, WSGI | `config/settings.py`, `config/urls.py` |
| `core` | Home page and shared form helpers | `core/views.py`, `core/urls.py` |
| `accounts` | Registration, profile, authentication, wallets | `accounts/models.py`, `accounts/services.py`, `accounts/views.py` |
| `products` | Categories and product catalog | `products/models.py`, `products/views.py` |
| `cart` | Persistent carts for users and sessions | `cart/models.py`, `cart/services.py`, `cart/views.py` |
| `wishlist` | User wishlists | `wishlist/models.py`, `wishlist/views.py` |
| `orders` | Checkout, payment, order history, fulfillment workflow | `orders/models.py`, `orders/views.py`, `orders/workflow.py` |
| `notifications` | In-app and external order notifications | `notifications/models.py`, `notifications/services.py` |
| `reviews` | Product ratings and comments | `reviews/models.py`, `reviews/views.py` |
| `dashboard` | Admin, seller, and delivery operational views | `dashboard/views.py`, `dashboard/decorators.py` |

Installed third-party Django-adjacent services are not separate apps: email uses Django's email backend, WhatsApp uses optional Twilio settings, and payments are local simulator classes.

## 5. Root URL Map

Defined in `config/urls.py`:

| Prefix | Included app |
|---|---|
| `/admin/` | Django admin |
| `/` | `core` |
| `/accounts/` | Account features |
| `/products/` | Catalog |
| `/cart/` | Cart |
| `/wishlist/` | Wishlist |
| `/orders/` | Checkout and orders |
| `/notifications/` | Notifications |
| `/reviews/` | Reviews |
| `/dashboard/` | Role-based management dashboard |
| `/accounts/` | Django's built-in auth URLs are also included |

Important named routes include:

- Products: `/products/`, `/products/categories/`, `/products/category/<slug>/`, `/products/<slug>/`
- Cart: `/cart/`, `/cart/add/<product_id>/`, `/cart/update/<item_id>/`, `/cart/remove/<item_id>/`
- Accounts: `/accounts/login/`, `/accounts/register/`, `/accounts/profile/`, `/accounts/wallet/`
- Orders: `/orders/checkout/`, `/orders/payment/`, `/orders/success/<order_number>/`, `/orders/history/`, `/orders/<order_number>/transition/<new_status>/`
- Notifications: `/notifications/`, `/notifications/<notification_id>/read/`
- Reviews: `/reviews/save/<product_id>/`, `/reviews/delete/<pk>/`

## 6. Data Model

### Accounts

- Django's built-in `auth.User` is the user model.
- `accounts.Profile` is one-to-one with `User` and stores `role`, phone, address, city, and postal code.
- Profile roles are `BUYER`, `SELLER`, `DELIVERY`, and `ADMIN`; default is `BUYER`.
- `accounts.Wallet` is one-to-one with `User`, has a non-negative decimal balance, and updates `updated_at`.
- `accounts.WalletTransfer` records sender, recipient, amount, optional note, generated unique `WAL-...` reference, and creation time.

### Catalog and shopping

- `products.Category`: unique name and slug, optional image, alphabetic ordering.
- `products.Product`: category, name, slug, description, price, optional discount price, stock, image, optional seller, brand, unique SKU, featured/active flags, and timestamps.
- `Product.current_price` returns `discount_price` when present, otherwise `price`.
- `Product.objects.active()` filters active products.
- `cart.Cart`: either one authenticated user or one anonymous session key.
- `cart.CartItem`: cart/product/quantity with a unique `(cart, product)` constraint and computed total.
- `wishlist.Wishlist`: one-to-one with a user and many-to-many with products.
- `reviews.Review`: product/user/rating/comment/timestamps with one review per `(product, user)`.

### Orders

- `orders.Order` has a generated unique `ORD-...` number.
- An order belongs to a buyer (`user`, nullable on deletion), may have a protected `seller`, and may have a delivery person.
- It snapshots customer delivery details and item totals so order history is not dependent on later product edits.
- Payment fields include `payment_method`, `is_paid`, `payment_reference`, `transaction_hash`, and `transaction_signature`.
- Available payment methods: `CARD`, `KHALTI`, `ESEWA`, and `COD`.
- `orders.OrderItem` stores product, product name snapshot, price snapshot, and quantity; its `total` is price multiplied by quantity.
- Order timestamps include accepted, ready, picked up, delivered, and completed times.

### Notifications

- `notifications.Notification` belongs to a recipient and optionally an order.
- Types cover order placement, each fulfillment stage, cancellation, and completion.
- Notifications are newest-first and have an `is_read` flag.

## 7. Checkout and Payment Behavior

Checkout is authenticated-user oriented and uses the current cart. Payment gateway classes in `orders/payment_gateway.py` are demonstrations only and do not contact payment networks:

| Method | Demo success values |
|---|---|
| Card | `4111 1111 1111 1111`, expiry `12/30`, CVV `123` |
| Khalti-style | ID `9800000000`, MPIN `1111` |
| eSewa-style | ID `9800000001`, password `Nepal@123`, OTP `123456` |
| Cash on delivery | No upfront credentials; payment is marked successful for collection on delivery |

Invalid demo credentials return a declined result and should not create the paid order. Successful payments receive a generated demo reference. The order transaction payload is canonicalized and protected with a SHA-256 hash plus an HMAC-SHA256 signature derived from `SECRET_KEY`. Verification is implemented by `orders.security.verify_transaction_signature`.

Do not describe these gateway classes as production payment integrations. A real provider callback/server-side signature check is required before production order creation or status changes.

## 8. Order State Machine

The authoritative transition rules are in `orders/workflow.py`:

```text
PLACED -> ACCEPTED -> PREPARING -> READY_FOR_DELIVERY -> ASSIGNED
ASSIGNED -> PICKED_UP -> OUT_FOR_DELIVERY -> DELIVERED -> COMPLETED
```

Cancellation is allowed from `PLACED`, `ACCEPTED`, or `PREPARING` by the assigned seller. A seller may also directly move `PREPARING -> ASSIGNED` by choosing a delivery rider; the normal path is `READY_FOR_DELIVERY -> ASSIGNED`, where a delivery user claims the job.

Required actors:

- Seller: accept, prepare, mark ready, and cancel their own assigned orders.
- Delivery person: claim an unassigned ready order, pick it up, mark it out for delivery, and mark it delivered after assignment.
- Buyer: confirm delivery, moving `DELIVERED -> COMPLETED`.
- Admin: dashboard/admin access may be available, but workflow authorization still matters; inspect the view/service before assuming an override exists.

Each transition updates relevant timestamps, creates in-app notifications for involved users, and may queue email/WhatsApp notifications after database commit. Notifications also include a confirmation to the actor who performed the transition.

## 9. Wallet Transfers

`accounts.services.transfer_funds` performs peer-to-peer transfers inside an atomic transaction. It locks both wallets in deterministic user-ID order, rejects self-transfers and insufficient balances, updates both balances, and creates a `WalletTransfer`. Each account receives a wallet through account setup/signals; administrator funding is intended to be done from Django admin for demonstration purposes.

## 10. Roles and Access Control

`dashboard/decorators.py` provides `admin_required`, `seller_required`, and `delivery_required`. Superusers bypass these role checks; admins are allowed through seller and delivery dashboard decorators. The order workflow separately checks the user's `Profile.role`, assigned seller, assigned delivery person, and buyer identity.

Dashboard areas:

- `/dashboard/`: admin home, user/product/category/order management, notification settings.
- `/dashboard/seller/`: seller home, owned products, seller orders, notification test.
- `/dashboard/delivery/`: available deliveries, assigned deliveries, delivery detail, notification test.

## 11. Notifications and Environment Settings

Default email backend is the console backend. External delivery is disabled unless channels are configured. Relevant settings include:

```env
SECRET_KEY=replace-with-a-secure-value
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000
DATABASE_URL=postgresql://user:password@host:5432/database
ORDER_NOTIFICATION_CHANNELS=email,whatsapp
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=orders@example.com
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=orders@example.com
EMAIL_HOST_PASSWORD=replace-with-smtp-password
EMAIL_USE_TLS=True
TWILIO_ACCOUNT_SID=replace-with-account-sid
TWILIO_AUTH_TOKEN=replace-with-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
ADMIN_NOTIFY_ALL_ORDER_EVENTS=True
DEFAULT_PHONE_COUNTRY_CODE=+977
```

`ADMIN_NOTIFY_ALL_ORDER_EVENTS` defaults to true and controls whether admins receive all order-event external notifications. Provider failures are logged and should not roll back an order status change. WhatsApp numbers need international/E.164 formatting; the configured default country code is used for local numbers.

## 12. Security and Deployment Notes

- In production (`DEBUG=False`), secure session and CSRF cookies, HTTPS redirect, HSTS, `SECURE_PROXY_SSL_HEADER`, content-type sniffing protection, and same-origin referrer policy are enabled.
- Set a strong `SECRET_KEY`, real `ALLOWED_HOSTS`, and trusted CSRF origins before deployment.
- Do not store card numbers, CVV, gateway passwords, API tokens, or environment secrets in the database, Markdown files, source control, or logs.
- Media is served directly in debug and through Django's fallback media route otherwise; use a proper production media strategy for a real deployment.
- The payment system is intentionally a demo and must be replaced or augmented with provider-side verification for production.

## 13. Migration State

The repository currently contains migrations for:

- `accounts`: profile, wallet/transfer, roles, admin role support.
- `products`: initial catalog and product seller.
- `cart`, `wishlist`, `reviews`, `notifications`: initial schemas.
- `orders`: initial order schema, transaction proof, seller/delivery fields, status normalization, payment fields, and workflow timestamps.
- `dashboard`: no domain models; only an empty initial migration package.

After pulling schema changes, run `python manage.py migrate`. Avoid editing an already-applied migration unless there is a deliberate migration-repair plan.

## 14. Where To Look First When Debugging

1. Configuration or startup: `config/settings.py`, `config/urls.py`, `manage.py`.
2. Checkout/payment/order creation: `orders/views.py`, `orders/forms.py`, `orders/payment_gateway.py`, `orders/security.py`.
3. Status permissions and notifications: `orders/workflow.py`, `notifications/services.py`, `dashboard/decorators.py`.
4. Catalog behavior: `products/models.py`, `products/views.py`, `templates/products/`.
5. Cart identity and totals: `cart/services.py`, `cart/views.py`, `cart/models.py`.
6. User/wallet behavior: `accounts/views.py`, `accounts/services.py`, `accounts/signals.py`.
7. Presentation and shared context: `templates/base.html`, `static/css/site.css`, context processors in `cart`, `wishlist`, and `notifications`.

## 15. Documentation and Current Caveats

- `README.md` is the short operational guide.
- `SETUP_GUIDE.md` is a longer user/setup guide and may contain example credentials; treat those as local demonstration data only.
- `docs/BrewMart_User_Guide.md` is the generated/user-facing guide.
- There is no automated test suite visible in the repository tree; run `python manage.py check` and manually exercise checkout, role transitions, wallet transfers, notification polling, and admin flows after changes.
- Existing docs describe SQLite as development and PostgreSQL as production. The actual settings select PostgreSQL only when `DATABASE_URL` is set; otherwise they use SQLite.

## 16. Handoff Rules For Another AI

- Preserve existing Django app boundaries and use the existing service/workflow helpers before adding new abstractions.
- Treat `orders.workflow.TRANSITIONS` and `config/settings.py` as authoritative for state and configuration behavior.
- Check authorization and CSRF behavior whenever changing a POST endpoint.
- Use database transactions for balances, inventory/order creation, and other multi-record mutations.
- Do not expose or hardcode secrets. Keep demo payment credentials clearly marked as non-production.
- Before completing a change, run `python manage.py check`; run migrations and focused manual checks when models or workflows change.