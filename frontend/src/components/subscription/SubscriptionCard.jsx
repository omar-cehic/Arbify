
import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useAuth } from '../../hooks/useAuth';

const SubscriptionCard = () => {
    const { user } = useAuth();
    const [loading, setLoading] = useState(false);

    const handleUpgrade = async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            const response = await axios.post(
                `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/subscriptions/create-checkout-session`,
                {},
                { headers: { Authorization: `Bearer ${token}` } }
            );

            if (response.data.url) {
                window.location.href = response.data.url;
            } else {
                toast.error("Failed to start checkout session");
            }
        } catch (error) {
            console.error(error);
            toast.error("Error connecting to payment provider");
        } finally {
            setLoading(false);
        }
    };

    if (user?.subscription?.status === 'active') {
        return (
            <div className="bg-green-900/30 border border-green-500/50 rounded-lg p-6 text-center">
                <h3 className="text-xl font-bold text-green-400 mb-2">Pro Member</h3>
                <p className="text-gray-300">Your subscription is active. Enjoy full access!</p>
            </div>
        );
    }

    return (
        <div className="bg-gray-800 border border-yellow-500/50 rounded-lg p-6 shadow-xl max-w-sm mx-auto transform hover:scale-105 transition-transform duration-300">
            <div className="absolute top-0 right-0 bg-yellow-500 text-black text-xs font-bold px-2 py-1 rounded-bl-lg">
                MOST POPULAR
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">Arbify Pro</h3>
            <div className="flex items-baseline justify-center mb-6">
                <span className="text-4xl font-bold text-yellow-400">$39.99</span>
                <span className="text-gray-400 ml-1">/month</span>
            </div>
            <ul className="text-left text-gray-300 space-y-3 mb-8">
                <li className="flex items-center">
                    <span className="text-green-400 mr-2">✓</span> Real-time Arbitrage Alerts
                </li>
                <li className="flex items-center">
                    <span className="text-green-400 mr-2">✓</span> Unlimited Strategy Templates
                </li>
                <li className="flex items-center">
                    <span className="text-green-400 mr-2">✓</span> Advanced Calculator & Tracking
                </li>
                <li className="flex items-center">
                    <span className="text-green-400 mr-2">✓</span> All Sports (NFL, NBA, MLB, Soccer & more)
                </li>
                <li className="flex items-center">
                    <span className="text-green-400 mr-2">✓</span> Instant Email & Browser Notifications
                </li>
            </ul>
            <button
                onClick={handleUpgrade}
                disabled={loading}
                className="w-full bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-400 hover:to-yellow-500 text-black font-bold py-3 px-6 rounded-lg shadow-lg transition-all"
            >
                {loading ? 'Processing...' : 'Upgrade Now'}
            </button>
        </div>
    );
};

export default SubscriptionCard;
