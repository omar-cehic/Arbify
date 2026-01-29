import { useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Layout from './components/layout/Layout';
import PrivateRoute from './components/auth/PrivateRoute';
import Home from './pages/Home';
import Dashboard from './components/dashboard/Dashboard';
import Login from './components/auth/Login';
import RegisterForm from './components/auth/RegisterForm';
// VerifyEmail removed - users are auto-verified
import ForgotPassword from './components/auth/ForgotPassword';
import ResetPassword from './components/auth/ResetPassword';
import Subscription from './components/subscription/Subscription';
import Profile from './components/profile/Profile';
import BettingCalculator from './components/dashboard/BettingCalculator';
import ArbitrageFinder from './components/dashboard/ArbitrageFinder';
import notificationService from './services/notificationService';

import SubscriptionGate from './components/common/SubscriptionGate';
import { logPageView } from './utils/analytics';

// Legal pages
import TermsOfService from './pages/legal/TermsOfService';
import PrivacyPolicy from './pages/legal/PrivacyPolicy';
import RefundPolicy from './pages/legal/RefundPolicy';
import Support from './pages/Support';

// Not found page
const NotFound = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-900">
    <Helmet>
      <title>404 Not Found - Arbify</title>
      <meta name="description" content="Page not found." />
    </Helmet>
    <div className="bg-gray-800 p-8 rounded-lg shadow-lg max-w-md w-full text-center">
      <h2 className="text-2xl font-bold text-red-400 mb-4">404 - Page Not Found</h2>
      <p className="text-gray-300 mb-4">Sorry, the page you are looking for does not exist.</p>
      <a href="/" className="text-yellow-400 hover:text-yellow-500">Go Home</a>
    </div>
  </div>
);

export default function App() {
  const location = useLocation();

  useEffect(() => {
    logPageView(location.pathname + location.search);
  }, [location]);

  // Global Notification Polling
  useEffect(() => {
    // Attempt to start polling using saved preferences
    const savedPrefs = localStorage.getItem('userPreferences');
    if (savedPrefs) {
      try {
        const prefs = JSON.parse(savedPrefs);
        if (prefs.notification_browser) {
          notificationService.startPolling(prefs);
        }
      } catch (e) {
        console.error('Failed to parse preferences for notifications:', e);
      }
    }

    return () => {
      // Create a cleanup function if needed, but we generally want polling to persist
      // unless specifically stopped or app unmounts.
      // notificationService.stopPolling(); 
    };
  }, []);

  return (
    <Layout>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<RegisterForm />} />
        {/* Email verification route removed - users are auto-verified */}
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/subscriptions" element={<Subscription />} />

        {/* Legal pages - public routes */}
        <Route path="/terms" element={<TermsOfService />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/refund-policy" element={<RefundPolicy />} />
        <Route path="/support" element={<Support />} />

        {/* Protected routes */}
        <Route path="/dashboard" element={
          <PrivateRoute>
            <SubscriptionGate pageName="the dashboard">
              <Dashboard />
            </SubscriptionGate>
          </PrivateRoute>
        } />
        <Route path="/profile" element={
          <PrivateRoute>
            <Profile />
          </PrivateRoute>
        } />

        <Route path="/arbitrage" element={
          <PrivateRoute>
            <SubscriptionGate pageName="arbitrage opportunities">
              <ArbitrageFinder />
            </SubscriptionGate>
          </PrivateRoute>
        } />
        <Route path="/calculator" element={
          <PrivateRoute>
            <SubscriptionGate pageName="the arbitrage calculator">
              <BettingCalculator />
            </SubscriptionGate>
          </PrivateRoute>
        } />

        {/* Not found route */}
        <Route path="*" element={<NotFound />} />
      </Routes>
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
        toastClassName="!bg-gray-800 !text-gray-100 !border !border-yellow-500/50 !rounded-lg !shadow-xl"
        progressClassName="!bg-yellow-500"
      />
    </Layout>
  );
}