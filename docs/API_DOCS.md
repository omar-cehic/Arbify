# API Documentation

This document lists the available API endpoints for the Arbify platform.

## Base URL
Development: `http://localhost:8000`
Production: `https://your-railway-app.up.railway.app`

## Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| POST | `/register` | Register a new user | No |
| POST | `/token` | Login (Get Access Token) | No |
| GET | `/me` | Get current user details | Yes |
| GET | `/me/profile` | Get user profile preferences | Yes |
| PUT | `/me/profile` | Update user profile | Yes |
| POST | `/me/change-password` | Change password | Yes |
| POST | `/reset-password` | Reset password (Legacy) | Yes |

## Subscriptions (`/api/subscription`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| GET | `/plans` | Get all available subscription plans | No |
| GET | `/plans/{plan_id}` | Get specific plan details | No |
| POST | `/checkout` | Create Stripe checkout session | Yes |
| POST | `/checkout-trial` | Create trial checkout session | Yes |
| POST | `/activate-trial` | Activate trial after payment | Yes |
| POST | `/cancel` | Cancel current subscription | Yes |
| GET | `/my-subscription` | Get current user's subscription | Yes |
| GET | `/my-payments` | Get payment history | Yes |
| POST | `/webhook` | Stripe Webhook Handler | No |

## Arbitrage & Odds (`/api`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| GET | `/odds/live/{sport_key}` | Get live odds for a sport | Yes |
| GET | `/admin/validate-current-opportunities` | Get validated arbitrage opportunities | Yes (Admin) |
| POST | `/admin/trigger-odds-update` | Manually trigger odds update | Yes (Admin) |

## User Management

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| GET | `/me/transactions` | Get user transaction history | Yes |
| GET | `/me/strategies` | Get user arbitrage strategies | Yes |
| POST | `/me/strategies` | Create new strategy | Yes |
| DELETE | `/me` | Deactivate account | Yes |

## Debug & Testing (Dev Only)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/admin/scheduler-status` | Check background scheduler |
| GET | `/admin/test-sgo-key` | Test SGO API key |
| GET | `/test-debug` | Debug API data structure |
| GET | `/debug-auth` | Test authentication |

## Data Models

### User
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": true
}
```

### Subscription Plan
```json
{
  "id": 1,
  "name": "Premium",
  "price_monthly": 59.99,
  "features": [...]
}
```
