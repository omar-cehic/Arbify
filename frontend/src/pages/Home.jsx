import React from 'react';
import Hero from '../components/common/Hero';
import { Helmet } from 'react-helmet-async';

const Home = () => {
  return (
    <>
      <Helmet>
        <title>Arbify - Arbitrage Betting Platform</title>
        <meta name="description" content="Find profitable arbitrage opportunities across multiple bookmakers and maximize your returns with Arbify." />
      </Helmet>
      <Hero />
    </>
  );
};

export default Home; 