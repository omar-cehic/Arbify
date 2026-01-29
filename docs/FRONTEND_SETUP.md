# Frontend Setup Guide

This guide provides detailed instructions for setting up the Arbify frontend (React/Vite).

## Prerequisites

- **Node.js 16+**: Ensure Node.js and npm are installed.

## Installation Steps

1.  **Navigate to Frontend Directory**
    ```bash
    cd frontend
    ```

2.  **Install Dependencies**
    ```bash
    npm install
    ```

3.  **Environment Configuration**
    Create a `.env` file in the `frontend` directory if needed (Vite uses `.env` files).
    
    ```env
    VITE_API_URL=http://localhost:8000
    VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
    ```

4.  **Run Development Server**
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

## Project Structure

- `src/components/`: Reusable UI components.
- `src/pages/`: Page components corresponding to routes.
- `src/context/`: React Context for global state (Auth, etc.).
- `src/hooks/`: Custom React hooks.
- `src/utils/`: Utility functions (API client, formatting).

## Building for Production

To build the application for production deployment:

```bash
npm run build
```

This will create a `dist` directory with optimized assets ready for deployment to Vercel, Netlify, or any static host.
