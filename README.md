# BrewMart Django E-commerce

## Install
1. Create and activate a virtual environment.
2. Run `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set a secure `SECRET_KEY` and PostgreSQL `DATABASE_URL`.
4. Create the PostgreSQL database, then run `python manage.py migrate`.
5. Run `python manage.py createsuperuser` and `python manage.py runserver`.

Use `/admin/` to add categories and products. Production uses environment variables, WhiteNoise static delivery, secure cookies and HTTPS settings when `DEBUG=False`.

## Payment demonstration

Checkout uses a local Khalti-style gateway simulator so the complete online card flow can be demonstrated without contacting a payment network. In production, `SecurityMiddleware` redirects HTTP to HTTPS when `DEBUG=False`, secure cookies prevent session and CSRF cookies from crossing plain HTTP, and `SECURE_PROXY_SSL_HEADER` supports a trusted TLS-terminating reverse proxy.

1. Sign in, add a product to the cart, and open checkout.
2. Submit the delivery details to open the payment page.
3. Use card number `4111 1111 1111 1111`, expiry `12/30`, and CVV `123`.
4. The approved response displays a demo transaction reference and then links to the order.

Any other card details produce a declined response while leaving the cart unchanged. Card number and CVV are used only during the request and are never stored. After approval, the server creates a canonical transaction payload, displays its SHA-256 hash, and stores an HMAC-SHA256 signature made with `SECRET_KEY`. The reusable verifier is `orders.security.verify_transaction_signature`; a production gateway must additionally verify the provider's own server-side callback or signature before creating the order or changing its status. HMAC is a symmetric application signature for this demonstration, not a replacement for a provider's asymmetric digital-signature scheme.

## Digital wallet demonstration

Run `python manage.py migrate` after pulling the wallet changes. Each account receives a stored-value wallet with a zero starting balance. An administrator can add demonstration funds from `/admin/` by editing a user's Wallet record.

To simulate a peer-to-peer transfer, sign in as the funded user, open **Account > Open wallet and transfer funds**, enter the second user's username and an amount, then submit. Both wallet balances update atomically, a transfer reference is recorded, and transfers larger than the available balance are rejected.

## Order workflow demonstration

Profiles support `BUYER`, `SELLER`, and `DELIVERY` roles. An administrator assigns roles in `/admin/` and assigns a seller to each product. Paid orders start at `PLACED`; the workflow service enforces these transitions:

`PLACED` -> `ACCEPTED` -> `PREPARING` -> `READY_FOR_DELIVERY` -> `ASSIGNED` -> `PICKED_UP` -> `OUT_FOR_DELIVERY` -> `DELIVERED` -> `COMPLETED`

Role-protected POST transitions are available at `/orders/<order_number>/transition/<status>/`. For example, a seller can post to `/orders/ORD-.../transition/accepted/` only for that seller's placed order. Invalid transitions, wrong roles, and delivery reassignment are rejected. Each successful transition creates database notifications for the relevant users.

### Order email and WhatsApp notifications

Accepted (confirmed) and cancelled orders can also notify the buyer by email, WhatsApp, or both. External delivery is disabled by default. Add these settings to `.env` to enable it:

```env
ORDER_NOTIFICATION_CHANNELS=email,whatsapp
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=orders@example.com
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=orders@example.com
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=True
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

The WhatsApp recipient must be stored as an international phone number, such as `+977...`, and must be permitted by the configured WhatsApp sender. For a Twilio sandbox, the recipient must first join the sandbox. Provider failures are logged and do not block or roll back the order status change.

Notifications can initially be polled with `GET /notifications/`; the response is limited to the authenticated user's notifications. Mark one read with `POST /notifications/<id>/read/`. Both endpoints require login, and the read endpoint also requires CSRF protection.
