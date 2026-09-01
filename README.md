# BrewMart Django E-commerce

## Install
1. Create and activate a virtual environment.
2. Run `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set a secure `SECRET_KEY` and PostgreSQL `DATABASE_URL`.
4. Create the PostgreSQL database, then run `python manage.py migrate`.
5. Run `python manage.py createsuperuser` and `python manage.py runserver`.

Use `/admin/` to add categories and products. Production uses environment variables, WhiteNoise static delivery, secure cookies and HTTPS settings when `DEBUG=False`.

## Payment demonstration

Checkout uses a local Khalti-style gateway simulator so the complete online card flow can be demonstrated without contacting a payment network:

1. Sign in, add a product to the cart, and open checkout.
2. Submit the delivery details to open the payment page.
3. Use card number `4111 1111 1111 1111`, expiry `12/30`, and CVV `123`.
4. The approved response displays a demo transaction reference and then links to the order.

Any other card details produce a declined response while leaving the cart unchanged. Card number and CVV are used only during the request and are never stored. For production, replace `orders/payment_gateway.py` with Khalti/eSewa API calls and verify the server-side callback before creating the order or changing its status.

## Digital wallet demonstration

Run `python manage.py migrate` after pulling the wallet changes. Each account receives a stored-value wallet with a zero starting balance. An administrator can add demonstration funds from `/admin/` by editing a user's Wallet record.

To simulate a peer-to-peer transfer, sign in as the funded user, open **Account > Open wallet and transfer funds**, enter the second user's username and an amount, then submit. Both wallet balances update atomically, a transfer reference is recorded, and transfers larger than the available balance are rejected.
