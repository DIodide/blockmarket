import React from 'react';

const FeaturesSection = () => {
  const features = [
    {
      icon: "🤖",
      title: "AI-Powered Trading",
      description: "Advanced algorithms optimize every trade"
    },
    {
      icon: "⚡",
      title: "Real-time Visualization",
      description: "Watch trades happen in beautiful Minecraft worlds"
    },
    {
      icon: "🎯",
      title: "Optimal Strategies",
      description: "Custom models designed for bartering economies"
    }
  ];

  return (
    <div className="features">
      {features.map((feature, index) => (
        <div key={index} className="feature">
          <div className="feature-icon">{feature.icon}</div>
          <h3>{feature.title}</h3>
          <p>{feature.description}</p>
        </div>
      ))}
    </div>
  );
};

export default FeaturesSection;
