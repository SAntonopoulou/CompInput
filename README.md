# Comprehensible Input Crowdfunding Platform

A web application that connects language learners with teachers. Learners can crowdfund specific "Comprehensible Input" video content, and teachers can get paid to create content that students actually want.

## Features

*   **Crowdfunding Campaigns:** Teachers create project proposals with funding goals.
*   **Pledges:** Students pledge money via Stripe to fund projects.
*   **Video Delivery:** Teachers upload videos to fulfilled projects; backers get notified.
*   **Request Board:** Students can request specific topics, and teachers can convert these requests into projects.
*   **Dashboards:** Dedicated dashboards for Teachers (manage projects, payouts) and Students (track pledges).
*   **Stripe Connect:** Automated payouts to teachers when projects are completed.

## Tech Stack

*   **Backend:** Python, FastAPI, SQLModel (SQLite for dev), Stripe API.
*   **Frontend:** React, Vite, Tailwind CSS.
*   **Authentication:** OAuth2 with JWT (Argon2 password hashing).
*   **Payments:** Stripe Connect & Payment Intents.

## Prerequisites

*   Python 3.9+
*   Node.js 16+
*   A Stripe Account (for Test Mode API keys)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd compinput
```

### 2. Backend Setup

Navigate to the backend folder, set up the virtual environment, and install dependencies.

```bash
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Windows: .venv\Scripts\activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Configuration:**
Create a `.env` file in the `backend/` directory:

```ini
# backend/.env
SECRET_KEY=your_super_secure_random_secret_key
STRIPE_SECRET_KEY=sk_test_...  # Get from Stripe Dashboard
STRIPE_WEBHOOK_SECRET=whsec_... # Get from Stripe CLI or Dashboard
FRONTEND_URL=http://localhost:5173
```

**Run the Server:**

```bash
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`.
The Docs will be available at `http://localhost:8000/docs`.

### 3. Frontend Setup

Open a new terminal, navigate to the frontend folder, and install dependencies.

```bash
cd frontend

# Install dependencies
npm install
```

**Configuration:**
Create a `.env` file in the `frontend/` directory:

```ini
# frontend/.env
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLIC_KEY=pk_test_... # Get from Stripe Dashboard
```

**Run the Frontend:**

```bash
npm run dev
```
The application will be available at `http://localhost:5173`.

### 4. Stripe Webhook Setup (Optional but Recommended)

To test automatic project funding updates when a payment succeeds, you need the Stripe CLI.

1.  Install Stripe CLI.
2.  Login: `stripe login`
3.  Forward webhooks to your local backend:

```bash
stripe listen --forward-to localhost:8000/pledges/webhook
```

4.  Copy the `whsec_...` signing secret output by the CLI and paste it into your `backend/.env` file as `STRIPE_WEBHOOK_SECRET`.

## Default User Roles

When registering a new user via the frontend:
*   Select **Student** to browse and pledge.
*   Select **Teacher** to create projects and receive payouts.