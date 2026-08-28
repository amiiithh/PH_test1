# PosterHub 🎨

A full-stack e-commerce website for selling wall posters — built with **Django** and **Razorpay** (test mode).
Created as an MCA final-year project, inspired by [posterized.in](https://www.posterized.in).

---

## Features

- **Product catalog** — categories/collections, product listing with sort & pagination, search, product detail pages with size-based pricing (A4 / A3 / A2)
- **Cart** — works for guests (session-based) and logged-in users (DB-based); guest cart automatically merges into the account cart on login/signup
- **Accounts** — registration, login, logout, password change, profile page with saved addresses and recent orders
- **Checkout & Payments** — multi-step checkout (address → payment), real **Razorpay Checkout.js** integration in **test mode**, server-side payment signature verification, order confirmation/failure pages
- **Order management** — order history, order detail, status tracking (Pending / Paid / Shipped / Delivered / Cancelled)
- **Admin panel** — Django admin fully configured to manage categories, products (with stock/discount/bestseller flags), and orders (with bulk "mark shipped/delivered" actions)
- **Custom design** — hand-built "gallery wall" visual identity (no UI framework/Bootstrap), responsive down to mobile

---

## Tech Stack

| Layer          | Technology                              |
|-----------------|------------------------------------------|
| Backend         | Django 6.1 (Python)                     |
| Database        | SQLite (default) or PostgreSQL          |
| Payments        | Razorpay (test mode) via `razorpay` SDK |
| Frontend        | Django Templates + hand-written CSS/JS  |
| Images          | Pillow (for `ImageField` processing)    |

---

## Project Structure

```
posterhub/
├── posterhub/          # project settings, root urls.py
├── store/               # catalog: Category, Product, Cart, CartItem
│   └── management/commands/seed_store.py   # demo data generator
├── orders/              # Address, Order, OrderItem, checkout & Razorpay views
├── accounts/             # registration/login/profile, Profile model
├── templates/            # all HTML templates (base.html + per-app folders)
├── static/css/style.css  # the entire design system, hand-written
├── requirements.txt
├── .env.example          # copy to .env and fill in your values
└── manage.py
```

### Data model (simplified)

```
Category ─┬─< Product >─┬─< CartItem >── Cart ── User
          │              │
          │              └─< OrderItem >── Order ── Address ── User
          └── (self-contained)
```

- One `Cart` per user (or per guest session); a `CartItem` snapshots product + size + quantity.
- Placing an order copies cart items into `OrderItem` rows (with a `product_name` snapshot) so the order stays intact even if a product is later edited or deleted.
- `Order` stores Razorpay's `order_id`, `payment_id` and `signature` for traceability/audit — useful to show in your project report.

---

## Setup Instructions

### 1. Clone/copy the project and create a virtual environment

```bash
cd posterhub
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and, at minimum, set a `SECRET_KEY`. Leave `USE_POSTGRES=False` to use SQLite — no extra setup needed. See the **PostgreSQL** and **Razorpay** sections below for those two optional steps.

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. (Optional but recommended) Seed demo data

This generates 6 categories and ~36 products with placeholder poster artwork — no internet required — so the site looks complete immediately:

```bash
python manage.py seed_store
```

### 6. Create an admin account

```bash
python manage.py createsuperuser
```

### 7. Run the server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** for the storefront and **http://127.0.0.1:8000/admin/** for the admin panel.

---

## Setting up Razorpay (test mode — no real money involved)

1. Sign up free at **https://dashboard.razorpay.com/signup**
2. In the dashboard, toggle **Test Mode** (top-right switch)
3. Go to **Settings → API Keys → Generate Test Key**
4. Copy the **Key Id** and **Key Secret** into your `.env`:
   ```
   RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxxx
   RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
   ```
5. Restart the server.

### Testing a payment

At the payment step, Razorpay's Checkout popup will appear. Use any of these **official test credentials** (no real money moves):

- **Card:** `4111 1111 1111 1111`, any future expiry date, any 3-digit CVV, any name
- **UPI:** `success@razorpay` (simulates a successful payment) or `failure@razorpay` (simulates a failed one)

Full list of test instruments: https://razorpay.com/docs/payments/payments/test-card-upi-details/

### How the payment flow works (for your viva/report)

1. `orders:checkout` — user picks/enters a delivery address → stored in the session.
2. `orders:payment` — server creates an `Order` (status `PENDING`) and a matching Razorpay Order via the API, then renders Razorpay's Checkout.js.
3. The user pays inside the Razorpay popup. Razorpay redirects the browser to `orders:payment_verify` with `razorpay_order_id`, `razorpay_payment_id`, and `razorpay_signature`.
4. The server **recomputes the HMAC-SHA256 signature using the secret key** and compares it — this is what actually proves the payment is genuine (this is why that view is marked `@csrf_exempt`: the POST originates from Razorpay's redirect, not from a form on our own site, so Django's CSRF token isn't present; the signature check is what replaces it as the authenticity guarantee).
5. On success, the order is marked `PAID`, the cart is emptied, and the user is sent to the confirmation page.

---

## Switching to PostgreSQL

1. Install PostgreSQL locally and create a database, e.g. `createdb posterhub`
2. In `.env`, set:
   ```
   USE_POSTGRES=True
   DB_NAME=posterhub
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```
3. Install the driver: `pip install psycopg2-binary`
4. Run `python manage.py migrate` again.

---

## Default login (only if you loaded the included demo database)

If you kept the pre-seeded `db.sqlite3` that ships with this project:
- **Admin:** username `admin`, password `admin12345` — **change this immediately if you deploy anywhere public.**

If you ran `migrate` fresh, use `createsuperuser` instead (recommended).

---

## Deploying (brief notes)

This ships configured for local development. Before deploying anywhere public:
- Set `DEBUG=False` and a real, random `SECRET_KEY` in `.env`
- Set `ALLOWED_HOSTS` to your real domain
- Run `python manage.py collectstatic` and serve `staticfiles/` via your web server or a service like WhiteNoise
- Serve `media/` (product images) from real storage (e.g. AWS S3) rather than local disk in production
- Use PostgreSQL rather than SQLite
- Use your **live** Razorpay keys only once you've completed Razorpay's KYC/activation — until then, keep using test keys

---

## Ideas for extending this project

- Wishlist / "save for later"
- Product reviews & ratings
- Coupon codes / discounts at checkout
- Order tracking with shipment status emails
- Razorpay webhooks (`/orders/webhook/`) as a second, more robust source of truth for payment status, in addition to the redirect-based verification already implemented
- REST API (Django REST Framework) if you want a separate mobile app later

---

Built as an academic project. Payments run through Razorpay's official test mode — no real transactions occur unless you switch to live API keys.
