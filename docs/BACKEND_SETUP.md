# Backend Setup Guide

This guide provides detailed instructions for setting up the Arbify backend (Python/FastAPI).

## Prerequisites

- **Python 3.9+**: Ensure Python is installed and added to your PATH.
- **Git**: For version control.
- **PostgreSQL** (Optional): For production database, or use SQLite for development.

## Installation Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/omar-cehic/Arbify.git
    cd Arbify
    ```

2.  **Create a Virtual Environment**
    It's recommended to use a virtual environment to manage dependencies.
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration**
    Create a `environ.env` file in the root directory. You can copy the example:
    ```bash
    cp environ.env.example environ.env
    ```
    
    **Required Variables:**
    ```env
    # Database (Default: SQLite)
    DATABASE_URL=sqlite:///./arbitrage.db
    
    # Security
    SECRET_KEY=generate-a-secure-random-string
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    
    # SportsGameOdds API (Required for odds data)
    SGO_API_KEY=your_sgo_api_key_here
    
    # Email (Resend)
    RESEND_API_KEY=re_...
    EMAIL_FROM=notifications@arbify.net
    
    # Stripe (Optional for dev, required for payments)
    STRIPE_SECRET_KEY=sk_test_...
    STRIPE_PUBLISHABLE_KEY=pk_test_...
    STRIPE_WEBHOOK_SECRET=whsec_...
    
    # Frontend URL (For CORS)
    FRONTEND_URL=http://localhost:5173
    ```

5.  **Initialize Database**
    Run the initialization script to create tables:
    ```bash
    python create_tables.py
    ```
    
    *Note: If using Alembic for migrations:*
    ```bash
    alembic upgrade head
    ```

6.  **Run the Server**
    Start the FastAPI development server:
    ```bash
    python main.py
    ```
    The server will start at `http://localhost:8000`.

## Project Structure

- `main.py`: Application entry point.
- `api.py`: Main API router and logic.
- `auth.py`: Authentication utilities (JWT, hashing).
- `user_routes.py`: User management endpoints.
- `subscription_routes.py`: Subscription and payment endpoints.
- `models/`: Database models (if separated).
- `alembic/`: Database migration scripts.

## Troubleshooting

- **Missing Dependencies**: If you encounter `ModuleNotFoundError`, ensure your virtual environment is active and run `pip install -r requirements.txt` again.
- **Database Errors**: If using SQLite, ensure the directory is writable. If using PostgreSQL, check your connection string.
