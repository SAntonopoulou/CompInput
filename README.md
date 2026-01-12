# FastAPI and React Project

This project is a bootstrap for a web application with a Python FastAPI backend and a React frontend.

## Backend

The backend is a FastAPI application located in the `backend` directory.

### Setup and Running

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the development server:
    ```bash
    uvicorn main:app --reload
    ```
    The application will be available at `http://127.0.0.1:8000`.

## Frontend

The frontend is a React application built with Vite and styled with Tailwind CSS, located in the `frontend` directory.

### Setup and Running

1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install the Node.js dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.
