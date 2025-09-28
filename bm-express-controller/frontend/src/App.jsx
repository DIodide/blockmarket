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
  const [editingInventories, setEditingInventories] = useState(new Map());
  
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
      // Merge editing inventories to global atom before starting simulation
      const newInventories = new Map(inventories);
      editingInventories.forEach((inventory, cellKey) => {
        newInventories.set(cellKey, { ...inventory });
      });
      setInventories(newInventories);
      
      // Filter inventories to only include currently selected cells
      const selectedInventories = new Map();
      selectedCells.forEach(cellKey => {
        if (newInventories.has(cellKey)) {
          selectedInventories.set(cellKey, newInventories.get(cellKey));
        }
      });
      
      console.log('Selected inventories for simulation:', Object.fromEntries(selectedInventories));
      
      const success = startSimulation(selectedInventories);
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
      const initial_inventory = {"diamond":0, "gold":0, "apple":0, "emerald":0, "redstone":0}
      newInventories.set(cellKey, initial_inventory);
    }
    setInventories(newInventories);
    setSelectedCells(newSelectedCells);
  };

  const handleClearSelection = () => {
    setSelectedCells(new Set());
    // Clear inventories for cells that are no longer selected
    setInventories(new Map());
    setEditingInventories(new Map());
  };

  const handleBackToInput = () => {
    setShowGrid(false);
  };

  const handleEditingInventoriesChange = (newEditingInventories) => {
    setEditingInventories(newEditingInventories);
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
            onEditingInventoriesChange={handleEditingInventoriesChange}
          />
        )}
        
        {!showGrid && <FeaturesSection />}
      </div>
    </div>
  );
}

export default App;