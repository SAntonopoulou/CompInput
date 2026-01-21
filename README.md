# Comprehensible Input Crowdfunding Platform

A web application that connects language learners with teachers. Learners can crowdfund specific "Comprehensible Input" video content, and teachers can get paid to create content that students actually want.

## Features
### 🎓 For Learners (Students)
*   **Discover Content:** Browse proposed video projects by language and level (JLPT, CEFR). **Search** by title or description.
*   **Request Board:** Can't find what you need? Post a request.
    *   Set a budget.
    *   Target specific teachers or leave it open.
    *   **Private Requests:** Option to keep requests between you and a teacher.
    *   **Negotiation:** Accept or reject counter-offers from teachers.
*   **Crowdfunding:** Pledge money securely via Stripe to fund projects.
*   **Track Progress:** Dashboard to view backed projects, watch embedded videos with auto-generated thumbnails, and read project updates.
*   **Confirm Completion:** Confirm a project is complete to approve the teacher's payout, ensuring accountability.
*   **Rate & Review:** Rate completed projects to help others find quality teachers.
*   **Profile:** Showcase your **Current Ability** with a demo video link and **Avatar**.

### 👨‍🏫 For Instructors (Teachers)
*   **Create Campaigns:** Propose video series with funding goals and delivery timelines.
*   **Get Paid:** Secure payouts via Stripe Connect once projects are completed.
*   **Manage Workflow:** Dashboard to track funding, upload videos, request completion from students, and manage requests.
*   **Build Reputation:** Public profile showing past work, average ratings, **Intro Video**, **Teaching Samples**, and a dedicated page for all reviews.
*   **Showcase Credentials:** Get verified for language certifications and display badges on your profile to stand out.
*   **Find Work:** Browse student requests and offer to fulfill them.
*   **Engage:** Post and edit status updates to projects, and reply to student reviews.

### 💬 Community & Discovery
*   **Interaction:** Comment sections on videos for Q&A.
*   **Tags:** Filter projects by interests (e.g., Gaming, Grammar, Travel).
*   **Updates:** Teachers can post and edit text updates to keep backers informed during production.
*   **Project Archive:** A public library of all successfully completed projects to discover teachers and content.
*   **Teacher Reviews Page:** A dedicated page to view all of a teacher's ratings and comments.
*   **Related Projects:** Smart suggestions for similar content on project pages.

### 🛡️ Admin
*   **Dashboard:** View platform statistics (Users, Projects, Funds).
*   **Teacher Verification:** Review and approve/reject teacher certification submissions.
*   **Moderation:** Delete users or cancel projects if necessary.

### ⚙️ Platform Features
*   **Secure Auth:** JWT authentication with Argon2 password hashing.
*   **Notifications:** Real-time alerts for funding goals, new videos, and offers.
*   **Safety:** Automated refunds if a project is cancelled.
*   **Student-Approved Payouts:** A two-step payout process that requires student confirmation, building trust.
*   **Enhanced Privacy:** Cancelled and draft projects are hidden from public view, only accessible to authorized users.
*   **Responsive UI:** Built with React and Tailwind CSS for all devices.
*   **UX Enhancements:** Toast notifications and confirmation modals for a smooth experience.
*   **Account Safety:** "Soft delete" functionality to preserve project history even if a user leaves.
*   **Scalability:** Pagination and optimized database queries for high performance.
*   **Search:** Global text search for projects.

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
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure_admin_password
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
VITE_TIKTOK_URL=https://www.tiktok.com
VITE_INSTAGRAM_URL=https://www.instagram.com
VITE_BLUESKY_URL=https://bsky.app
VITE_X_URL=https://x.com
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

## 🚀 Project Status & To Do

The application is currently **Feature Rich**. All core logic for project creation, funding, requests, payouts, administration, and reputation management (ratings, reviews, verifications) is implemented.

### Future Enhancements & To-Do List

#### Infrastructure & Polish
- [ ] **Email Integration:** Integrate an email service (e.g., SendGrid, Mailgun) for:
  - User email verification upon registration.
  - Secure password reset functionality.
  - Offline notifications for important events (e.g., project funded, payout processed).
- [ ] **Direct File Uploads:** Integrate a cloud storage service (e.g., AWS S3, Cloudinary) for:
  - User avatars.
  - Teacher intro/sample videos.
  - Secure hosting for delivered project videos, replacing the current URL-pasting system.
  - Teacher certification documents.
- [ ] **Deployment & Scalability:**
  - Create `Dockerfile` and `docker-compose.yml` for containerized deployment.
  - Set up a production-ready PostgreSQL database.
- [ ] **Legal & Compliance:**
  - Add "Terms of Service" and "Privacy Policy" pages, which are required for a live Stripe account.