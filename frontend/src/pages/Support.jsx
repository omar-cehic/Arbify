import React from 'react';
import { Helmet } from 'react-helmet-async';

const Support = () => {
    return (
        <div className="min-h-screen bg-gray-900 text-gray-300 py-12 px-4 sm:px-6 lg:px-8 flex items-center justify-center">
            <Helmet>
                <title>Support - Arbify Arbitrage Betting</title>
                <meta name="description" content="Contact Arbify support for help with your account, subscription, or arbitrage betting questions." />
            </Helmet>

            <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-xl p-8 border border-gray-700 text-center">
                <div className="mb-6">
                    <div className="w-16 h-16 bg-yellow-400/10 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">Contact Support</h1>
                    <p className="text-gray-400">We're here to help with any questions or issues.</p>
                </div>

                <div className="bg-gray-900/50 rounded-lg p-6 border border-gray-700 mb-6">
                    <p className="text-sm text-gray-500 mb-2 uppercase tracking-wide font-semibold">Email Us At</p>
                    <a href="mailto:support@arbify.net" className="text-xl font-bold text-yellow-400 hover:text-yellow-300 transition-colors break-words">
                        support@arbify.net
                    </a>
                </div>

                <div className="text-sm text-gray-500">
                    <p>We typically respond within 24 hours.</p>
                    <p className="mt-2">For immediate assistance with subscriptions, please visit the <a href="/subscriptions" className="text-yellow-400 hover:underline">Subscription Management</a> page.</p>
                </div>
            </div>
        </div>
    );
};

export default Support;
