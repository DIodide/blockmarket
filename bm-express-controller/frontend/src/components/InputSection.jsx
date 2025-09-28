import React from 'react';

const InputSection = ({ 
  playAreaSize, 
  setPlayAreaSize, 
  showGrid, 
  onCreateGrid 
}) => {
  return (
    <div className="input-section">
      <div className="input-group">
        <label htmlFor="playAreaSize" className="input-label">
          Play Area Size
        </label>
        <input
          id="playAreaSize"
          type="number"
          value={playAreaSize}
          onChange={(e) => setPlayAreaSize(e.target.value)}
          placeholder="Enter size (e.g., 50)"
          className="play-area-input"
          min="10"
          max="200"
        />
        <span className="input-hint">Note: only 10x10 grid with 5 agents is supported right now</span>
      </div>
      
      {!showGrid && (
        <button 
          onClick={onCreateGrid}
          className="start-button"
          disabled={!playAreaSize}
        >
          Create Grid
        </button>
      )}
    </div>
  );
};

export default InputSection;
