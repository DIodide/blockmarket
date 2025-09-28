import React from 'react';

const Grid = ({ 
  playAreaSize, 
  selectedCells, 
  onToggleCell, 
  onClearSelection, 
  onBackToInput, 
  onStartSimulation, 
  isConnected 
}) => {
  const renderGrid = () => {
    const size = parseInt(playAreaSize);
    const grid = [];
    
    for (let row = 0; row < size; row++) {
      for (let col = 0; col < size; col++) {
        const cellKey = `${row}-${col}`;
        const isSelected = selectedCells.has(cellKey);
        
        grid.push(
          <div
            key={cellKey}
            className={`grid-cell ${isSelected ? 'selected' : ''}`}
            onClick={() => onToggleCell(row, col)}
            title={`Cell (${row}, ${col})`}
          />
        );
      }
    }
    
    return grid;
  };

  return (
    <div className="grid-section">
      <h3>Select Areas for Trading ({selectedCells.size} selected)</h3>
      <div 
        className="grid-container" 
        style={{
          gridTemplateColumns: `repeat(${parseInt(playAreaSize)}, 1fr)`,
          gridTemplateRows: `repeat(${parseInt(playAreaSize)}, 1fr)`
        }}
      >
        {renderGrid()}
      </div>
      <div className="grid-controls">
        <div className="grid-controls-top">
          <button 
            onClick={onClearSelection}
            className="clear-button"
          >
            Clear Selection
          </button>
          <button 
            onClick={onBackToInput}
            className="back-button"
          >
            Back to Size Input
          </button>
        </div>
        <button 
          onClick={onStartSimulation}
          className="start-button"
          disabled={!isConnected || selectedCells.size === 0}
        >
          {isConnected ? `Start Simulation (${selectedCells.size} cells)` : 'Connecting...'}
        </button>
      </div>
    </div>
  );
};

export default Grid;
