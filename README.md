 # CompInput Platform
 
 A dynamic platform designed to connect language learners with teachers who create comprehensible input video projects. Students can request custom content, fund projects, and engage with teachers, while teachers can showcase their skills, receive funding, and build a community around their language expertise.
 
 ## Features
 
 This platform offers a rich set of functionalities for both students and teachers:
 
 ### User Management & Authentication
 - Secure user registration and login with JWT authentication.
 - Distinct user roles: Student, Teacher, and Admin.
 - Customizable user profiles with bio, languages, and avatar.
 - Teachers can add introduction and sample video URLs to their profiles.
 - Account deletion with data anonymization for GDPR compliance.
 - Teacher language verification system with admin approval workflow.
 
 ### Project Lifecycle & Funding
 - **Flexible Project Creation:** Teachers can create single-video or multi-video series projects.
 - **Customizable Project Presentation:**
     - Teachers can set a custom image for their projects, overriding default video thumbnails.
     - Series projects can have a dedicated introduction video.
 - **Dynamic Pricing:** Projects can be funded with a total goal or a price-per-video model for series.
 - **Stripe Integration:**
     - Secure student pledges via Stripe Checkout.
     - Stripe Connect for seamless teacher payouts, with platform fees automatically collected.
     - Tipping feature: Users can send tips to teachers on successful/completed projects.
 - **Project Progress & Updates:**
     - Real-time funding progress tracking.
     - Teachers can post updates to their projects, notifying backers.
     - Automatic project updates when new videos are linked.
 - **Video Management:**
     - Teachers can upload videos directly from the project page or dashboard.
     - Server-side validation ensures the correct number of videos are uploaded for single or series projects.
     - Teachers can link supplementary resources (PDFs, links) to individual videos.
 - **Completion & Review:**
     - Student confirmation of project completion to release funds.
     - Project rating and review system for backers (always visible for completed projects).
     - Dynamic project delivery status display (Projected vs. Actual Delivered days).
 - **Admin Oversight:**
     - Tools for project management, including cancellation.
     - Automated cleanup of abandoned projects (from deleted teachers).
 
 ### Request & Offer System
 - Students can post detailed content requests (single video or series).
 - Teachers can initiate conversations to discuss requests.
 - **Comprehensive Offers:** Teachers can make detailed project offers within the chat, including:
     - Title, description, price, language, level, tags.
     - Series details (is_series, number of videos, price per video).
 - **Interactive Offers:** Offers appear as interactive messages in chat, allowing students to accept or reject.
 - **Automated Workflows:**
     - **Offer Acceptance:** Automatically creates a new project, closes all related conversations, and redirects to the new project page.
     - **Offer Rejection:** Closes the current conversation and blacklists the teacher from that request.
     - **Request Cancellation:** Students can cancel their requests, closing associated conversations.
 - Dedicated "My Requests" page for students, separating open and accepted requests.
 
 ### Real-time Messaging (Conversations)
 - Teacher-initiated, request-specific conversations.
 - Real-time chat with WebSockets for instant message delivery.
 - Reply-to-message functionality for organized discussions.
 - Teacher can request student demo videos; students can submit URLs within the chat.
 - Conversation closure (teacher-controlled, student-leave, offer acceptance/rejection).
 - Archived conversations for historical reference.
 - Smart, context-aware notifications for new messages (global unread count, conversation-specific).
 
 ### Social & Community Features
 - **Teacher Following:**
     - Students can follow teachers they admire.
     - Followers receive notifications for new projects by followed teachers.
     - Teacher profiles display follower count and a ranked list of followers (by pledge amount).
     - Student profiles display teachers they are following, ranked by their contributions, with unfollow capability.
     - Follow/Unfollow actions available on profiles and project cards.
 - **Language Groups:**
     - Users (students/teachers) can join language-specific community groups.
     - Groups are dynamically available based on active/completed projects in that language.
     - Group members receive notifications for new projects in their group's language.
     - User profiles display joined language groups.
     - Dedicated "Groups" page to discover and manage memberships.
 
 ### UI/UX Enhancements
 - Improved modal positioning and input field styling for better readability.
 - Consistent and intuitive navigation.
 
 ## Getting Started
 
 Follow these instructions to set up and run the project locally.
 
 ### Prerequisites
 - Python 3.14+
 - Node.js (LTS version)
 - npm or yarn
 - Git
 - Stripe Account (for payment processing)
 
 ### 1. Clone the Repository
 
 ```bash
 git clone <repository_url>
 cd CompInput
 ```
 
 ### 2. Backend Setup
 
 Navigate to the `backend` directory:
 
 ```bash
 cd backend
 ```
 
 **a. Create a Python Virtual Environment and Install Dependencies:**
 ```bash
 python -m venv .venv
 source .venv/bin/activate  # On Windows: .venv\Scripts\activate
 pip install -r requirements.txt
 ```
 
 *(Note: You may need to create a `requirements.txt` file by running `pip freeze > requirements.txt` after installing all necessary packages like `fastapi`, `sqlmodel`, `uvicorn`, `python-dotenv`, `stripe`, `psycopg2-binary` (if using PostgreSQL), etc.)*
 
 **b. Environment Variables:**
 Create a `.env` file in the `backend` directory with the following variables:
 
 ```
 DATABASE_URL="sqlite:///./database.db" # Or your PostgreSQL connection string
 SECRET_KEY="your_super_secret_key_for_jwt"
 ALGORITHM="HS256"
 ACCESS_TOKEN_EXPIRE_MINUTES=30
 
 STRIPE_SECRET_KEY="sk_test_..." # Your Stripe secret key
 STRIPE_WEBHOOK_SECRET="whsec_..." # Your Stripe webhook secret (from Stripe CLI)
 PLATFORM_FEE_PERCENT=0.15 # 15% platform fee on pledges and tips
 
 FRONTEND_URL="http://localhost:5173" # URL where your frontend is running
 
 ADMIN_EMAIL="admin@example.com"
 ADMIN_PASSWORD="adminpassword"
 ```
 
 ### 3. Frontend Setup
 
 Navigate to the `frontend` directory:
 
 ```sh
 cd ../frontend
 ```
 
 **a. Install Node.js Dependencies:**
 
 ```sh
 npm install # or yarn install
 ```
 
 **b. Environment Variables:**
 Create a `.env` file in the `frontend` directory:
 
 ```
 VITE_API_URL="http://localhost:8000" # URL where your backend is running
 ```
 
 ### 4. Running the Application
 
 **a. Start the Backend:**
 From the `backend` directory:
 
 ```sh
 uvicorn backend.main:app --reload
 ```
 
 The backend will be accessible at `http://localhost:8000`.
 
 **b. Start the Frontend:**
 From the `frontend` directory:
 
 ```sh
 npm run dev # or yarn dev
 ```
 
 The frontend will typically be accessible at `http://localhost:5173`.
 
 ### 5. Stripe Webhook Configuration
 
 To handle Stripe events (like successful pledges and tips), you need to set up a webhook.
 
 **a. Install Stripe CLI:**
 Follow the instructions on the Stripe documentation to install the CLI.
 
 **b. Forward Webhooks:**
 In a new terminal, from your project's root directory (or any directory), run:
 
 ```sh
 stripe listen --forward-to http://localhost:8000/pledges/webhook
 ```
 
 This will output a `whsec_...` secret. Copy this secret and add it to your `backend/.env` file as `STRIPE_WEBHOOK_SECRET`.
 
 ## Contributing
 
 ... (Instructions for contributing)
 