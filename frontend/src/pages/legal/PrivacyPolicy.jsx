import React from 'react';

import { Helmet } from 'react-helmet-async';

const PrivacyPolicy = () => {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-300 py-12 px-4 sm:px-6 lg:px-8">
      <Helmet>
        <title>Privacy Policy - Arbify</title>
        <meta name="description" content="Learn how Arbify collects, uses, and protects your personal data." />
      </Helmet>
      <div className="max-w-4xl mx-auto bg-gray-800 rounded-lg shadow-xl p-8 border border-gray-700">
        <h1 className="text-3xl font-bold text-yellow-400 mb-8 border-b border-gray-700 pb-4">Privacy Policy</h1>

        <div className="space-y-6">
          <p>
            Arbify ("we," "us," or "our"), operated by Arbify LLC, is committed to protecting your privacy. This Privacy Policy explains what information we collect, how we use and share it, and your rights regarding your data. By using Arbify's website or related services (the "Service"), you acknowledge that you are at least 18 years of age, legally able to participate in online gambling activities in your jurisdiction, not located in a prohibited jurisdiction, and agree to the practices described here. You further represent that you are not a prohibited person under any applicable anti-money laundering, anti-terrorism, or sanctions laws.
          </p>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">1. Information We Collect</h2>
            <div className="ml-4 space-y-4">
              <div>
                <h3 className="text-lg font-medium text-yellow-400">1.1. Personal Data</h3>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li><strong>Account Information:</strong> Name, email, password (hashed).</li>
                  <li><strong>Financial Information:</strong> Payment processing is handled by Stripe in compliance with PCI-DSS requirements. We maintain records of transactions as required by law for anti-money laundering compliance, but never store complete payment card details.</li>
                  <li><strong>Contact Info:</strong> Email address for support and notifications.</li>
                </ul>
              </div>
              <div>
                <h3 className="text-lg font-medium text-yellow-400">1.2. Usage Data</h3>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li><strong>Device Info:</strong> IP address, browser, OS, device type.</li>
                  <li><strong>Activity Logs:</strong> Pages visited, features used, clickstream data.</li>
                  <li><strong>Error Tracking:</strong> Logs via tools like Sentry.</li>
                </ul>
              </div>
              <div>
                <h3 className="text-lg font-medium text-yellow-400">1.3. Cookies & Trackers</h3>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li><strong>Essential Cookies:</strong> For authentication and security.</li>
                  <li><strong>Analytics:</strong> Google Analytics.</li>
                  <li><strong>Emails:</strong> May include open/click tracking via Resend.</li>
                </ul>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">2. How We Use Data</h2>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li>Provide and maintain the Service</li>
              <li>Process payments (via Stripe)</li>
              <li>Communicate with users</li>
              <li>Analyze usage and improve performance</li>
              <li>Ensure legal compliance and security</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">3. Sharing & Disclosure</h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-white">Service Providers</h3>
                <p>We engage trusted third-party service providers including payment processors (Stripe), hosting providers (Vercel, Railway), odds data providers (TheOddsAPI), monitoring services (Sentry), email services (Resend), and analytics (Google Analytics). All service providers are bound by strict contractual obligations regarding data protection, confidentiality, and compliance with applicable gambling regulations.</p>
              </div>
              <div>
                <h3 className="text-lg font-medium text-white">Legal and Regulatory Compliance</h3>
                <p>We may disclose your information if required by law, regulation, or legal process, including but not limited to gambling regulatory authorities, law enforcement requests, court orders, or to protect our rights, property, or safety, or that of our users or others. We may also share information to comply with anti-money laundering regulations and to prevent fraud or other illegal activities.</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">4. Data Retention</h2>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li><strong>Account Data:</strong> Retained as long as your account is active.</li>
              <li><strong>Financial Records:</strong> Retained for a minimum of 7 years to comply with tax laws, gambling regulations, anti-money laundering requirements, and other applicable legal obligations.</li>
              <li><strong>Logs:</strong> Retained up to 90 days (raw); anonymized versions may be kept longer.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">5. Security</h2>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li>Encryption in transit and at rest</li>
              <li>Role-based access controls</li>
              <li>Regular dependency audits</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">6. Your Rights</h2>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li><strong>Access/Update:</strong> You may update your account info at any time.</li>
              <li><strong>Deletion:</strong> You may request account deletion by contacting us.</li>
              <li><strong>Cookies:</strong> Manage preferences via your browser.</li>
              <li><strong>Unsubscribe:</strong> Opt out of marketing emails at any time.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">7. Children's Privacy</h2>
            <p>Arbify is not intended for users under 18 (or 21+ where applicable). If we learn we've collected data from someone underage, we will delete it.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">8. International Transfers</h2>
            <p>Your data may be processed in the United States or in other countries where our service providers maintain operations. Any international transfer of your personal data will be conducted in accordance with applicable laws and regulations, including but not limited to Standard Contractual Clauses, and appropriate technical and organizational security measures will be maintained. By using our Service, you consent to your information being transferred to and processed in these locations.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">9. Policy Updates</h2>
            <p>We may update this policy periodically. Changes take effect once posted. Continued use indicates acceptance.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-2">10. Contact Us</h2>
            <p>Arbify LLC</p>
            <p>Attn: Privacy Officer</p>
            <p>Email: <a href="mailto:support@arbify.net" className="text-yellow-400 hover:underline">support@arbify.net</a></p>
          </section>

          <div className="text-sm text-gray-500 mt-8 pt-4 border-t border-gray-700">
            <p>Questions? Contact us at <a href="mailto:support@arbify.net" className="text-yellow-400 hover:underline">support@arbify.net</a></p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
