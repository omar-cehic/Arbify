import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import Button from './Button';
import Logo from './Logo';

const features = [
  {
    icon: <i className="fas fa-search text-yellow-400 text-3xl"></i>,
    title: 'Real-Time Arbitrage Scanner',
    desc: 'Advanced algorithms continuously scan for profitable arbitrage opportunities across multiple markets.'
  },
  {
    icon: <i className="fas fa-calculator text-yellow-400 text-3xl"></i>,
    title: 'Advanced Betting Calculator',
    desc: 'Calculate optimal stake distribution and potential profits with precision for any arbitrage opportunity.'
  },
  {
    icon: <i className="fas fa-chart-bar text-yellow-400 text-3xl"></i>,
    title: 'Comprehensive Odds Comparison',
    desc: 'Compare odds across multiple bookmakers to identify the most profitable betting opportunities.'
  },
  {
    icon: <i className="fas fa-tachometer-alt text-yellow-400 text-3xl"></i>,
    title: 'Professional Dashboard',
    desc: 'Manage your arbitrage strategies, track performance, and access all tools from one central location.'
  },
];

const faqs = [
  {
    question: "What is arbitrage betting and how does it work?",
    answer: "Arbitrage betting is a strategy that exploits price differences between bookmakers to guarantee profit regardless of the outcome. When different sportsbooks offer varying odds on the same event, you can bet on all possible outcomes and secure a profit. Arbify finds these opportunities automatically, so you don't have to manually compare hundreds of odds."
  },
  {
    question: "How much money can I make with arbitrage betting?",
    answer: "Profit margins typically range from 1-8% per arbitrage opportunity. While this might seem small, it compounds quickly with consistency. Most users see 10-25% monthly returns on their bankroll when actively using arbitrage strategies."
  },
  {
    question: "Do I need accounts with multiple bookmakers?",
    answer: "Yes, having accounts with multiple sportsbooks is essential for arbitrage betting. The more bookmakers you have access to, the more opportunities you'll find. We recommend starting with at least 5-7 major sportsbooks, and many offer sign-up bonuses that can boost your initial bankroll."
  },
  {
    question: "Is arbitrage betting legal and safe?",
    answer: "Yes, arbitrage betting is completely legal. You're simply placing normal bets with licensed sportsbooks. However, some bookmakers may limit accounts if they detect consistent arbitrage betting, which is why having multiple accounts and varying your betting patterns is important."
  },
  {
    question: "What makes Arbify different from manual arbitrage hunting?",
    answer: "Manual arbitrage hunting is time-consuming and error-prone. Arbify automates the entire process by scanning thousands of odds across multiple bookmakers in real-time, calculating exact stakes, and alerting you instantly when profitable opportunities arise. This gives you a massive time advantage and ensures you never miss profitable bets."
  }
];

const scrollToHowItWorks = (e) => {
  e.preventDefault();
  const section = document.getElementById('how-it-works');
  if (section) {
    section.scrollIntoView({ behavior: 'smooth' });
  }
};

const Hero = () => {
  const { isAuthenticated } = useAuth();

  return (
    <>
      <div className="relative bg-gray-950 min-h-[700px] flex flex-col justify-between overflow-hidden">
        {/* Animated Overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-black/90 via-gray-900/80 to-yellow-900/60 z-10"></div>
        {/* Background Image */}
        <div className="absolute inset-0">
          <img
            className="w-full h-full object-cover opacity-60"
            src="/images/hero-bg.jpg"
            alt="Betting odds on multiple screens"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = 'https://placehold.co/1200x700/333/444?text=Betting+Background';
            }}
          />
        </div>
        {/* Content */}
        <div className="relative z-20 max-w-5xl mx-auto px-4 sm:px-8 flex flex-col items-center justify-center flex-1">
          {/* Logo */}
          <div className="mt-16 mb-6">
            <div className="flex flex-col items-center">
              <div className="relative">
                <Logo size="xl" />
                <div className="absolute bottom-0 right-0 bg-black text-yellow-400 text-xs font-bold px-1 rounded">BETA</div>
              </div>
              <div className="text-yellow-400 text-xs font-medium mt-2 tracking-widest">ARBITRAGE BETTING PLATFORM</div>
            </div>
          </div>
          {/* Headline */}
          <h1 className="text-4xl md:text-6xl font-extrabold text-white text-center mb-4">
            Turn Sports Betting Into <span className="text-yellow-400">Guaranteed Profit</span>
          </h1>
          {/* Subheadline */}
          <p className="text-lg md:text-2xl text-gray-200 text-center mb-8 max-w-2xl">
            Professional arbitrage tools for guaranteed betting profits.
          </p>
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link to={isAuthenticated ? "/dashboard" : "/register"}>
              <Button
                variant="primary"
                size="lg"
                className="shadow-lg focus:ring-yellow-300"
              >
                Get Started
              </Button>
            </Link>
            <Button
              variant="outline"
              size="lg"
              className="border-gray-600 bg-gray-900/80 hover:bg-gray-800 text-white"
              onClick={scrollToHowItWorks}
            >
              See How It Works
            </Button>
          </div>
          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full mb-20">
            {features.map((feature) => (
              <div key={feature.title} className="flex items-start gap-4 bg-gray-800/70 rounded-xl p-6 border border-yellow-400/60 hover:border-yellow-400 shadow-md hover:shadow-xl transition-all duration-300">
                <div>{feature.icon}</div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-1">{feature.title}</h3>
                  <p className="text-gray-300 text-sm md:text-base">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <section id="how-it-works" className="bg-gray-900 py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-8">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="flex flex-col items-center">
              <div className="bg-yellow-400 text-gray-900 rounded-full w-14 h-14 flex items-center justify-center text-2xl font-bold mb-4">1</div>
              <h3 className="text-lg font-semibold text-white mb-2">Sign Up</h3>
              <p className="text-gray-300">Create your free account to get started.</p>
            </div>
            <div className="flex flex-col items-center">
              <div className="bg-yellow-400 text-gray-900 rounded-full w-14 h-14 flex items-center justify-center text-2xl font-bold mb-4">2</div>
              <h3 className="text-lg font-semibold text-white mb-2">Set Preferences</h3>
              <p className="text-gray-300">Choose your favorite sports and bookmakers.</p>
            </div>
            <div className="flex flex-col items-center">
              <div className="bg-yellow-400 text-gray-900 rounded-full w-14 h-14 flex items-center justify-center text-2xl font-bold mb-4">3</div>
              <h3 className="text-lg font-semibold text-white mb-2">Get Alerts</h3>
              <p className="text-gray-300">Receive real-time arbitrage opportunities.</p>
            </div>
            <div className="flex flex-col items-center">
              <div className="bg-yellow-400 text-gray-900 rounded-full w-14 h-14 flex items-center justify-center text-2xl font-bold mb-4">4</div>
              <h3 className="text-lg font-semibold text-white mb-2">Profit!</h3>
              <p className="text-gray-300">Place your bets and maximize your returns.</p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-gray-950 py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-12 text-center">Frequently Asked Questions</h2>
          <div className="space-y-6">
            {faqs.map((faq, index) => (
              <div key={index} className="bg-gray-800/70 rounded-xl border border-yellow-400/60 hover:border-yellow-400 transition-colors">
                <details className="group">
                  <summary className="flex justify-between items-center cursor-pointer p-6 text-white hover:text-yellow-400 transition-colors">
                    <h3 className="text-lg font-semibold pr-4">{faq.question}</h3>
                    <i className="fas fa-chevron-down text-yellow-400 transform group-open:rotate-180 transition-transform"></i>
                  </summary>
                  <div className="px-6 pb-6">
                    <p className="text-gray-300 leading-relaxed">{faq.answer}</p>
                  </div>
                </details>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="bg-gray-900 py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-8">Need Help?</h2>
          <p className="text-gray-300 text-lg mb-8">
            Have questions about arbitrage betting or need technical support? We're here to help!
          </p>
          <div className="bg-gray-800/70 rounded-xl border border-yellow-400/60 p-8">
            <div className="flex flex-col md:flex-row items-center justify-center gap-6">
              <div className="text-center md:text-left">
                <h3 className="text-xl font-semibold text-white mb-2">Contact Support</h3>
                <p className="text-gray-300 mb-4">Get help with your account, billing, or technical issues</p>
                <a 
                  href="mailto:support@arbify.net" 
                  className="inline-flex items-center gap-2 bg-yellow-400 text-gray-900 px-6 py-3 rounded-lg font-semibold hover:bg-yellow-300 transition-colors"
                >
                  <i className="fas fa-envelope"></i>
                  support@arbify.net
                </a>
              </div>
              <div className="text-center md:text-left">
                <h3 className="text-xl font-semibold text-white mb-2">Legal & Policies</h3>
                <p className="text-gray-300 mb-4">Review our terms, privacy policy, and refund policy</p>
                <div className="flex flex-wrap gap-3 justify-center md:justify-start">
                  <a href="/terms" className="text-yellow-400 hover:text-yellow-300 underline text-sm">Terms of Service</a>
                  <span className="text-gray-600">|</span>
                  <a href="/privacy" className="text-yellow-400 hover:text-yellow-300 underline text-sm">Privacy Policy</a>
                  <span className="text-gray-600">|</span>
                  <a href="/refund-policy" className="text-yellow-400 hover:text-yellow-300 underline text-sm">Refund Policy</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default Hero; 