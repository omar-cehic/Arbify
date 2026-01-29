import React from 'react';

import { Helmet } from 'react-helmet-async';

const TermsOfService = () => {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-300 py-12 px-4 sm:px-6 lg:px-8">
      <Helmet>
        <title>Terms of Service - Arbify</title>
        <meta name="description" content="Read Arbify's Terms of Service regarding eligibility, user accounts, and liability." />
      </Helmet>
      <div className="max-w-4xl mx-auto bg-gray-800 rounded-lg shadow-xl p-8 border border-gray-700">
        <h1 className="text-3xl font-bold text-yellow-400 mb-8 border-b border-gray-700 pb-4">Terms of Service</h1>

        <div className="space-y-6">
          <section>
            <h2 className="text-xl font-semibold text-white mb-2">1. Acceptance of Terms</h2>
            <p>
              By accessing or using Arbify ("we," "us," "Service"), operated by Arbify LLC ("Operator"), you agree to be bound by these Terms of Service and acknowledge that these Terms create a legally binding contract. If you do not agree to any part of these Terms, you must immediately cease using Arbify.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">2. Eligibility & Age</h2>
            <p>
              You must be at least 18 years old (21+ where required) and capable of entering binding contracts. By using Arbify, you represent and warrant that you meet these requirements.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">3. Service Description & Disclaimers</h2>
            <p>
              Arbify provides information only about sports betting arbitrage opportunities. We do not accept bets, handle funds, or guarantee any results. All betting decisions are made at your own risk.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">4. Gambling Disclaimer</h2>
            <p>
              Arbify is a data and analytics platform only. We do not place bets, accept wagers, or handle user funds. You are solely responsible for ensuring that any betting activity you engage in is legal in your jurisdiction.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">5. User Accounts</h2>
            <p>
              You are responsible for maintaining the confidentiality of your account credentials. Notify us immediately of any unauthorized use.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">6. Intellectual Property</h2>
            <p>
              All content and code on Arbify are the property of Arbify LLC. You may not copy, distribute, or create derivative works without express permission.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">7. Payments, Subscriptions & Refunds</h2>
            <p>
              Premium features are billed via Stripe. We offer a satisfaction guarantee for new subscriptions within 14 days of your first paid charge (excluding free trial periods). After 14 days, subscription fees are non-refundable. You may cancel your subscription at any time, and no further charges will be made. For detailed refund information, see our Refund Policy.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">8. Earnings Disclaimer</h2>
            <p>
              Arbify does not guarantee earnings or profits. Arbitrage opportunities vary in frequency and reliability. Past performance does not indicate future results.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">9. Limitation of Liability & Indemnification</h2>
            <p>
              To the maximum extent permitted by law, Arbify LLC's total aggregate liability for any claims arising out of or related to these Terms shall not exceed the total fees paid by you to Arbify LLC in the previous 12 months. This limitation applies to all causes of action in the aggregate, including breach of contract, breach of warranty, negligence, strict liability, misrepresentation, and other torts. You agree to indemnify and hold harmless Arbify LLC from any third-party claims arising from your use of the service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">10. Governing Law</h2>
            <p>
              These Terms are governed by the laws of the State of Illinois, without regard to its conflict of law provisions.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">11. Changes to Terms</h2>
            <p>
              We may update these Terms at any time by providing at least 30 days' advance notice via email or in-app notification. The updated Terms will be effective no sooner than 30 days after such notice. Your continued use of Arbify after the effective date constitutes acceptance of the modified Terms. If you do not agree to the changes, you must discontinue using our services before the effective date.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">12. Contact Us</h2>
            <p>
              Email: <a href="mailto:arbify.app@gmail.com" className="text-yellow-400 hover:underline">arbify.app@gmail.com</a>
            </p>
          </section>

          <hr className="border-gray-700 my-8" />

          <h2 className="text-2xl font-bold text-white mb-4">Additional Disclaimers</h2>

          <section className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-2">A. Gambling Disclaimer</h3>
            <p>
              Arbify is a data and analytics platform only. We do not place bets, accept wagers, or handle user funds. You are solely responsible for ensuring that any betting activity you engage in is legal in your jurisdiction.
            </p>
          </section>

          <section className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-2">B. Geographic Restrictions</h3>
            <p>
              Use of Arbify is not permitted in jurisdictions where online sports betting or arbitrage activity is prohibited by law. Users are responsible for complying with all applicable federal, state, and local laws, including but not limited to the Illinois Sports Wagering Act and related regulations. Arbify reserves the right to verify user location and restrict access where legally required. By using our services, you represent and warrant that you are in compliance with all applicable laws in your region.
            </p>
          </section>

          <section className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-2">C. Earnings Disclaimer</h3>
            <p>
              Arbify does not guarantee earnings or profits. Arbitrage opportunities vary in frequency and reliability. Past performance does not indicate future results.
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

export default TermsOfService;
