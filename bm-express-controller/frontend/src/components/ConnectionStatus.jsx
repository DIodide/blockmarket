import React from 'react';

const ConnectionStatus = ({ isConnected }) => {
  return (
    <div className="connection-status">
      <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></div>
      <span>{isConnected ? 'Connected' : 'Connecting...'}</span>
    </div>
  );
};

export default ConnectionStatus;
