# Arbify - Professional Arbitrage Betting Platform

**A modern SaaS platform that automates sports arbitrage betting opportunities with real-time odds scanning, smart calculators, and subscription-based premium features.**

[![Status](https://img.shields.io/badge/Status-Beta-yellow.svg)](https://github.com/omar-cehic/Arbify)
[![License](https://img.shields.io/badge/License-Private-red.svg)](https://github.com/omar-cehic/Arbify)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)

---

## Project Overview

Arbify is a sophisticated web application that helps users identify and capitalize on sports arbitrage betting opportunities. The platform scans multiple sportsbooks in real-time, calculates optimal stake distributions, and provides professional tools for guaranteed profit betting strategies.

### Key Value Propositions:
- **Guaranteed Profits**: Mathematical arbitrage ensures profit regardless of game outcomes
- **Real-time Scanning**: Automated odds monitoring across multiple bookmakers
- **Professional Tools**: Advanced calculators, strategy management, and performance tracking
- **Simple Pricing**: All-inclusive subscription model

---

## System Architecture

```mermaid
graph TD
    Client[React Frontend (Vite)]
    API[FastAPI Backend (Railway)]
    DB[(PostgreSQL)]
    Queue[Asyncio Task Queue]
    SGO[SportsGameOdds API]
    Stripe[Stripe Payments]
    Email[Resend API]

    Client -->|JWT Auth| API
    Client -->|HTTPS| API
    API -->|Read/Write| DB
    API -->|Process Payments| Stripe
    API -->|Send Notifications| Email
    API -->|Schedule Tasks| Queue
    Queue -->|Poll Odds| SGO
    Queue -->|Update Odds| DB
```

---

## Tech Stack

### Frontend
- **React 18** - Modern component-based UI framework
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first styling framework
- **React Router** - Client-side navigation
- **Axios** - HTTP client for API communication
- **React Context** - State management for authentication

### Backend
- **Python 3.9+** - Core backend language
- **FastAPI** - High-performance async web framework
- **SQLAlchemy** - Python SQL toolkit and ORM
- **SQLite** - Development database
- **Alembic** - Database migration management
- **JWT** - Secure token-based authentication
- **bcrypt** - Password hashing and security

### Third-Party Services
- **Stripe** - Payment processing and subscription management
- **SportsGameOdds API** - Real-time sports betting odds data
- **Railway** - Backend hosting and database
- **Vercel** - Frontend hosting and CDN

### Development Tools
- **ESLint** - JavaScript linting
- **PostCSS** - CSS processing
- **Git** - Version control

---

## Features

### Core Functionality
- **Arbitrage Finder**: Real-time scanning for profitable betting opportunities
- **Smart Calculator**: Optimal stake distribution calculations
- **Odds Comparison**: Multi-bookmaker odds analysis
- **Strategy Management**: Custom arbitrage strategy creation and tracking

### User Management
- **Secure Authentication**: JWT-based login/registration system
- **Email Verification**: Account verification and password reset
- **Profile Management**: User preferences and account settings
- **Subscription Tracking**: Plan management and billing integration

### Subscription Tiers

#### Pro Plan ($49.99/month)
- Unlimited arbitrage opportunities (Pre-match & Live)
- Advanced calculator & stake sizing
- Unlimited custom strategies
- Real-time alerts (Email + Browser)
- High-speed odds refresh (30 seconds)
- Automated opportunity tracking

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Git

### Backend Setup
See [docs/BACKEND_SETUP.md](docs/BACKEND_SETUP.md) for detailed instructions.

```bash
# Clone repository
git clone https://github.com/omar-cehic/Arbify.git
cd Arbify

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp environ.env.example environ.env
# Edit environ.env with your configuration

# Initialize database
python create_tables.py

# Run development server
python main.py
```

### Frontend Setup
See [docs/FRONTEND_SETUP.md](docs/FRONTEND_SETUP.md) for detailed instructions.

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Environment Variables
Create `environ.env` file with:
```env
# Database
DATABASE_URL=sqlite:///./arbitrage.db

# JWT Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe (Payment Processing)
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email Configuration (Resend)
RESEND_API_KEY=re_...
EMAIL_FROM=notifications@arbify.net

# SportsGameOdds API
SGO_API_KEY=your-sgo-api-key

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

---

## Project Structure

```
arbify/
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   │   ├── auth/      # Authentication components
│   │   │   ├── common/    # Reusable components
│   │   │   ├── dashboard/ # Main app components
│   │   │   ├── layout/    # Layout components
│   │   │   ├── profile/   # User profile components
│   │   │   └── subscription/ # Billing components
│   │   ├── context/       # React context providers
│   │   ├── hooks/         # Custom React hooks
│   │   ├── pages/         # Page components
│   │   └── utils/         # Utility functions
│   ├── public/           # Static assets
│   ├── package.json         # Frontend dependencies
│   └── vite.config.js       # Vite configuration
├── alembic/              # Database migrations
├── venv/                 # Python virtual environment
├── main.py               # FastAPI application entry point
├── api.py                # API route definitions
├── auth.py               # Authentication logic
├── config.py             # Application configuration
├── db.py                 # Database connection setup
├── stripe_integration.py # Payment processing
├── user_routes.py        # User management APIs
├── subscription_routes.py # Subscription management APIs
├── arbitrage_notifications.py # Email notification system
├── user_models.py        # User database models
├── subscription_models.py # Subscription database models
├── mock_data.py          # Development data
├── requirements.txt      # Python dependencies
├── Procfile             # Railway deployment configuration
├── railway.json         # Railway settings
├── environ.env          # Environment variables
└── README.md            # This file
```

---

## API Endpoints

See [docs/API_DOCS.md](docs/API_DOCS.md) for full API documentation.

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/token` - User login
- `GET /api/auth/me` - Get current user
- `PUT /api/auth/user/profile` - Update user profile

### Subscriptions
- `GET /api/subscription/plans` - Get available plans
- `POST /api/subscription/checkout` - Create Stripe checkout session
- `GET /api/subscription/status` - Get user subscription status
- `POST /api/subscription/cancel` - Cancel subscription

### Arbitrage
- `GET /api/arbitrage/opportunities` - Get current opportunities
- `POST /api/user/arbitrage` - Save arbitrage opportunity
- `GET /api/user/arbitrage` - Get user's saved opportunities

---

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment guides.

### Production Setup
The application is configured for deployment on:
- **Backend**: Railway (Python/FastAPI)
- **Frontend**: Vercel (React/Vite)
- **Database**: PostgreSQL on Railway
- **Payments**: Stripe production environment

### Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway up
```

### Vercel Deployment
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy frontend
cd frontend
vercel --prod
```

---

## Development Workflow

### Running Locally
```bash
# Backend (Terminal 1)
python main.py

# Frontend (Terminal 2)
cd frontend && npm run dev
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

### Testing
```bash
# Run backend tests
python -m pytest

# Frontend development server
npm run dev
```

---

## Business Model

### Revenue Streams
- **Subscription Plans**: Single "Pro" tier at $49.99/month
- **Value Proposition**: All-inclusive access to professional arbitrage tools without upselling complexity

### Target Market
- Sports betting enthusiasts
- Professional arbitrage bettors
- Risk-averse investors seeking guaranteed returns
- Users in legal sports betting jurisdictions

---

## Security Features

- **JWT Authentication**: Secure token-based user sessions
- **Password Hashing**: bcrypt encryption for user passwords
- **Email Verification**: Account verification system
- **Rate Limiting**: API endpoint protection
- **Input Validation**: Pydantic schema validation
- **CORS Protection**: Cross-origin request security

---

## Future Roadmap

### Phase 1 (Current)
- [x] Core arbitrage functionality
- [x] User authentication and profiles
- [x] Stripe subscription integration
- [x] Email notification system
- [x] Real-time odds API integration (SGO)

### Phase 2 (Next)
- [ ] Mobile-responsive improvements
- [ ] Advanced analytics dashboard
- [ ] Social proof and testimonials

### Phase 3 (Future)
- [ ] Mobile app development
- [ ] Multi-language support
- [ ] Advanced user management
- [ ] Affiliate program

---

## Developer Notes

### Code Quality
- Clean, modular architecture
- Type hints throughout Python code
- Comprehensive error handling
- Responsive design principles
- Professional UI/UX design

### Performance
- Async FastAPI for high concurrency
- Optimized database queries
- CDN-hosted frontend assets
- Efficient React component structure

### Scalability
- Microservice-ready architecture
- Database migration system
- Environment-based configuration
- Cloud-native deployment

---

## Contact & Support

**Project Owner**: Omar Cehic  
**Status**: Beta Release  
**Last Updated**: January 2025
