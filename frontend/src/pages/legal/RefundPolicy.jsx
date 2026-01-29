import React from 'react';

import { Helmet } from 'react-helmet-async';

const RefundPolicy = () => {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-300 py-12 px-4 sm:px-6 lg:px-8">
      <Helmet>
        <title>Refund Policy - Arbify</title>
        <meta name="description" content="Review Arbify's refund policy, eligibility criteria, and process." />
      </Helmet>
      <div className="max-w-4xl mx-auto bg-gray-800 rounded-lg shadow-xl p-8 border border-gray-700">
        <h1 className="text-3xl font-bold text-yellow-400 mb-8 border-b border-gray-700 pb-4">Refund Policy</h1>

        <div className="space-y-6">
          <section>
            <h2 className="text-xl font-semibold text-white mb-2">14-Day Satisfaction Guarantee</h2>
            <p>
              At Arbify, we are confident in the value our arbitrage betting platform provides. We offer a fair refund policy to ensure your satisfaction while protecting our business from abuse.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-yellow-400 mb-4">REFUND ELIGIBILITY</h2>

            <div className="mb-4">
              <h3 className="text-lg font-medium text-white mb-2">Timeframe</h3>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>14 calendar days from your first paid subscription charge</li>
                <li>Free trial period does NOT count toward the 14-day window</li>
                <li>Refund window begins when your paid subscription starts (after trial ends)</li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-2">Qualifying Conditions</h3>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>You are dissatisfied with the service quality within the 14-day period</li>
                <li>You must request the refund via email to <a href="mailto:support@arbify.net" className="text-yellow-400 hover:underline">support@arbify.net</a></li>
                <li>Maximum one refund per customer per 12-month period</li>
                <li>Account must be in good standing (no violations of Terms of Service)</li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-yellow-400 mb-4">REFUND DETAILS</h2>

            <div className="mb-4">
              <h3 className="text-lg font-medium text-white mb-2">Refund Amount</h3>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>Full refund of the most recent subscription payment</li>
                <li>No partial or prorated refunds after the 14-day window</li>
              </ul>
            </div>

            <div className="mb-4">
              <h3 className="text-lg font-medium text-white mb-2">Processing Time</h3>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>Refunds are processed within 5-7 business days</li>
                <li>Refund processing may take up to 10 business days during high volume periods</li>
                <li>Refunds issued to your original payment method</li>
                <li>You will receive email confirmation when refund is processed</li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-2">Account Access During Refund Processing</h3>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>Account access is immediately suspended when refund is requested</li>
                <li>All Arbify services and features become unavailable during processing</li>
                <li>Access cannot be restored once refund processing begins</li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-yellow-400 mb-4">WHAT IS NOT COVERED</h2>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li>Free trial cancellations (trials are free - no refund needed)</li>
              <li>Requests made after 14 days from paid subscription start</li>
              <li>Second refund requests within 12 months</li>
              <li>Chargebacks or disputes (contact us first)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-yellow-400 mb-4">HOW TO REQUEST A REFUND</h2>
            <p className="mb-2">Email us at <a href="mailto:support@arbify.net" className="text-yellow-400 hover:underline">support@arbify.net</a></p>
            <p className="mb-2">Include:</p>
            <ul className="list-disc list-inside ml-4 space-y-1 mb-4">
              <li>Your account email address</li>
              <li>Reason for refund request</li>
              <li>Date of subscription payment</li>
            </ul>
            <p>We will respond within 24 hours. Refund processed within 5-7 business days if approved.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-yellow-400 mb-4">OUR COMMITMENT</h2>
            <p>
              We process legitimate refund requests quickly and fairly. Our goal is your satisfaction with Arbify's arbitrage opportunities and tools.
            </p>
          </section>

          <div className="text-sm text-gray-500 mt-8 pt-4 border-t border-gray-700">
            <p>Questions? Contact us at <a href="mailto:support@arbify.net" className="text-yellow-400 hover:underline">support@arbify.net</a></p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RefundPolicy;
