import React from 'react';

const HeroSection = () => {
  return (
    <div className="hero-content">
      <h1 className="hero-title">
        <span className="block-text">Block</span>
        <span className="market-text">Market</span>
      </h1>
      
      <p className="hero-subtitle">
        An interactive platform powered by our custom AI model
      </p>
      
      <p className="hero-description">
        Designed to make optimal trades in a bartering economy,
        <br />
        beautifully visualized through Minecraft
      </p>
    </div>
  );
};

export default HeroSection;
