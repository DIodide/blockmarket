import { useState } from 'react';
import {useAtom} from 'jotai';
import './App.css';

// Components
import ConnectionStatus from './components/ConnectionStatus';
import HeroSection from './components/HeroSection';
import InputSection from './components/InputSection';
import Grid from './components/Grid';
import FeaturesSection from './components/FeaturesSection';
// Atoms for inventory management
import { inventoriesAtom } from "./atoms/inventory";


// Hooks
import useSocket from './hooks/useSocket';

function App() {
  const [playAreaSize, setPlayAreaSize] = useState('');
  const [showGrid, setShowGrid] = useState(false);
  const [selectedCells, setSelectedCells] = useState(new Set());
  const [inventories, setInventories] = useAtom(inventoriesAtom);
  
  const { isConnected, startSimulation } = useSocket();

  const handleCreateGrid = () => {
    if (playAreaSize && parseInt(playAreaSize) >= 10 && parseInt(playAreaSize) <= 200) {
      setShowGrid(true);
      setSelectedCells(new Set());
      console.log(`Creating grid with size: ${playAreaSize}x${playAreaSize}`);
    } else {
      alert('Please enter a valid play area size (10-200)');
    }
  };

  const handleStartSimulation = () => {
    if (playAreaSize && isConnected && selectedCells.size > 0) {
      const success = startSimulation(playAreaSize, selectedCells);
      if (!success) {
        alert('Failed to start simulation. Please try again.');
      }
    } else if (!isConnected) {
      alert('Please wait for connection to server');
    } else if (selectedCells.size === 0) {
      alert('Please select at least one cell in the grid');
    } else {
      alert('Please enter a valid play area size');
    }
  };

  const toggleCell = (row, col) => {
    const cellKey = `${row}-${col}`;
    const newSelectedCells = new Set(selectedCells);
    const newInventories = new Map(inventories);
    
    if (newSelectedCells.has(cellKey)) {
      newSelectedCells.delete(cellKey);
      newInventories.delete(cellKey);
    } else {
      newSelectedCells.add(cellKey);
      const inital_inventory = {"diamond":0, "gold":0, "apple":0, "emerald":0, "redstone":0}
      newInventories.set(cellKey, inital_inventory);
    }
    setInventories(newInventories);
    setSelectedCells(newSelectedCells);
  };

  const handleClearSelection = () => {
    setSelectedCells(new Set());
  };

  const handleBackToInput = () => {
    setShowGrid(false);
  };

  return (
    <div className="App">
      <ConnectionStatus isConnected={isConnected} />
      
      <div className="hero-section">
        <HeroSection />
        
        <InputSection 
          playAreaSize={playAreaSize}
          setPlayAreaSize={setPlayAreaSize}
          showGrid={showGrid}
          onCreateGrid={handleCreateGrid}
        />
        
        {showGrid && (
          <Grid 
            playAreaSize={playAreaSize}
            selectedCells={selectedCells}
            onToggleCell={toggleCell}
            onClearSelection={handleClearSelection}
            onBackToInput={handleBackToInput}
            onStartSimulation={handleStartSimulation}
            isConnected={isConnected}
          />
        )}
        
        {!showGrid && <FeaturesSection />}
      </div>
    </div>
  );
}

export default App;