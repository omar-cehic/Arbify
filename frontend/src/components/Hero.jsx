import React from 'react';

const Hero = () => {
  return (
    <section className="relative bg-gray-900 overflow-hidden">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-black/70 to-black/50"></div>
      
      {/* Background image */}
      <div 
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage: "url('/static/images/hero-bg.jpg')",
          filter: 'blur(2px)'
        }}
      ></div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32">
        <div className="text-center">
          <div className="mb-8">
            <img 
              src="/static/images/arbify-logo.png" 
              alt="Arbify Logo" 
              className="h-32 mx-auto"
            />
          </div>
          
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6">
            Maximize Your Betting Profits
          </h1>
          
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
            Advanced arbitrage betting strategies powered by AI
          </p>
          
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <a 
              href="/subscription" 
              className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-lg text-gray-900 bg-yellow-400 hover:bg-yellow-500 transition-colors"
            >
              Get Started
            </a>
            <a 
              href="#features" 
              className="inline-flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-lg text-white hover:bg-gray-800 transition-colors"
            >
              Learn More
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero; 