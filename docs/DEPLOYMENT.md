# Deployment Guide

This guide covers deploying the Arbify platform to production using Railway (Backend) and Vercel (Frontend).

## Backend Deployment (Railway)

1.  **Install Railway CLI**
    ```bash
    npm install -g @railway/cli
    ```

2.  **Login to Railway**
    ```bash
    railway login
    ```

3.  **Deploy**
    Run the following command in the root directory:
    ```bash
    railway up
    ```

4.  **Configure Environment Variables**
    In the Railway dashboard, set the following variables:
    - `DATABASE_URL`: (Automatically set if you add a PostgreSQL plugin)
    - `SECRET_KEY`: Generate a strong random string.
    - `SGO_API_KEY`: Your SportsGameOdds API key.
    - `RESEND_API_KEY`: Your Resend API key.
    - `STRIPE_SECRET_KEY`: Stripe Production Secret Key.
    - `STRIPE_PUBLISHABLE_KEY`: Stripe Production Publishable Key.
    - `STRIPE_WEBHOOK_SECRET`: Stripe Webhook Secret.
    - `FRONTEND_URL`: The URL of your deployed frontend (e.g., `https://arbify.vercel.app`).
    - `ENVIRONMENT`: Set to `production`.

## Frontend Deployment (Vercel)

1.  **Install Vercel CLI**
    ```bash
    npm install -g vercel
    ```

2.  **Deploy**
    Navigate to the frontend directory and deploy:
    ```bash
    cd frontend
    vercel --prod
    ```

3.  **Configure Environment Variables**
    In the Vercel dashboard, set:
    - `VITE_API_URL`: The URL of your deployed backend (e.g., `https://arbify-production.up.railway.app`).
    - `VITE_STRIPE_PUBLISHABLE_KEY`: Stripe Production Publishable Key.

## Post-Deployment Verification

1.  **Check Health**: Visit your backend URL to ensure it's running.
2.  **Test Login**: Try logging in on the production frontend.
3.  **Test Payments**: Verify Stripe integration in production mode.
4.  **Verify Odds**: Ensure odds are being fetched from SGO API.
