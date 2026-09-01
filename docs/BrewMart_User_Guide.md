# BrewMart User Guide

## Purpose

BrewMart is a Django coffee shop application with user accounts, product browsing, shopping carts, wishlists, reviews, order history, a simulated Nepali payment gateway, and a stored-value digital wallet.

The payment gateway and wallet features are demonstrations for local development. They do not move real money.

## Start the application

1. Open a terminal in the project directory.
2. Activate the virtual environment if one is configured.
3. Install dependencies with `pip install -r requirements.txt`.
4. Apply database migrations with `python manage.py migrate`.
5. Start the site with `python manage.py runserver`.
6. Open `http://localhost:8000/`.

## Customer account

1. Select **Register** and create an account.
2. Sign in using the account credentials.
3. Open **Account** to update profile and shipping details.
4. The account receives a digital wallet automatically with a zero balance.

## Shopping and checkout

1. Open **Shop** or a product category.
2. Open a product and add it to the cart.
3. Open **Cart**, review quantities, and select checkout.
4. Sign in if requested.
5. Enter the delivery and contact details, then select **Continue to payment**.

## Demo card payment

The payment page is a local Khalti-style simulator. It does not contact Khalti, a bank, or a card network.

Use these values for an approved demonstration:

| Field | Demo value |
|---|---|
| Cardholder name | Any name |
| Card number | `4111 1111 1111 1111` |
| Expiry | `12/30` |
| CVV | `123` |

Select **Pay**. A successful response displays a `KHALTI-DEMO-...` transaction reference, creates the order, reduces product stock, and clears the cart.

To demonstrate a declined payment, enter any other card number. The cart remains unchanged and no order is created.

Card number and CVV are used only for the request and are never stored by this application.

## Digital wallet

The wallet is a stored-value balance denominated in Nepalese rupees. A wallet is created automatically for every new account. Existing accounts receive one when the wallet migration is applied.

### Fund a wallet for demonstration

1. Sign in to the Django admin at `http://localhost:8000/admin/`.
2. Open **Wallets**.
3. Select a user's wallet and enter a demonstration balance.
4. Save the wallet.

Only an administrator should fund wallets in this demonstration. There is no real deposit or withdrawal integration.

### Transfer between two accounts

1. Create or use two customer accounts.
2. Fund the sender's wallet from the admin panel.
3. Sign in as the sender.
4. Open **Account**, then **Open wallet and transfer funds**.
5. Enter the recipient's username, amount, and an optional note.
6. Select **Send funds**.
7. Review the balance and transfer reference in the wallet history.

The sender's balance decreases and the recipient's balance increases in one database transaction. Transfers larger than the available balance, transfers to an unknown username, and transfers to oneself are rejected. Each successful transfer receives a unique `WAL-...` reference.

## Useful routes

| Route | Use |
|---|---|
| `/` | Home page |
| `/products/` | Product catalogue |
| `/cart/` | Shopping cart |
| `/orders/checkout/` | Delivery details |
| `/orders/payment/` | Demo card payment |
| `/orders/history/` | Customer order history |
| `/accounts/register/` | Create an account |
| `/accounts/profile/` | Profile and wallet balance |
| `/accounts/wallet/` | Wallet transfers and history |
| `/admin/` | Product, order, and wallet administration |

## Important production boundary

Before production use, replace the local gateway simulator with the official Khalti or eSewa integration. Create a pending order, send the customer to the gateway, verify the server-side callback or lookup response, and only then finalize payment, stock, and order status. Never store full card numbers or CVV values.