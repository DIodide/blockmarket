import React, { useState, useEffect } from 'react';
import { useAtom } from 'jotai';
import { inventoriesAtom } from '../atoms/inventory';

const InventorySidePanel = ({ selectedCells, isVisible, onEditingInventoriesChange }) => {
  const [inventories, setInventories] = useAtom(inventoriesAtom);
  const [editingInventories, setEditingInventories] = useState(new Map());

  // Initialize editing inventories when selected cells change
  useEffect(() => {
    const newEditingInventories = new Map();
    const newInventories = new Map(inventories);
    let hasNewRandomData = false;
    
    selectedCells.forEach(cellKey => {
      // Check if we already have inventory data for this cell
      const existingInventory = inventories.get(cellKey);
      
      if (existingInventory) {
        // Use existing inventory data
        newEditingInventories.set(cellKey, { ...existingInventory });
      } else {
        // Generate random inventory values between 0 and 10
        const randomInventory = {
          diamond: Math.floor(Math.random() * 11), // 0-10
          gold: Math.floor(Math.random() * 11),
          apple: Math.floor(Math.random() * 11),
          emerald: Math.floor(Math.random() * 11),
          redstone: Math.floor(Math.random() * 11)
        };
        newEditingInventories.set(cellKey, randomInventory);
        newInventories.set(cellKey, randomInventory);
        hasNewRandomData = true;
      }
    });
    
    setEditingInventories(newEditingInventories);
    
    // Update the global inventories atom if we generated new random data
    if (hasNewRandomData) {
      setInventories(newInventories);
    }
  }, [selectedCells, inventories, setInventories]);

  // Notify parent component when editing inventories change
  useEffect(() => {
    if (onEditingInventoriesChange) {
      onEditingInventoriesChange(editingInventories);
    }
  }, [editingInventories, onEditingInventoriesChange]);

  const handleInventoryChange = (cellKey, itemType, value) => {
    const newEditingInventories = new Map(editingInventories);
    const cellInventory = newEditingInventories.get(cellKey) || {};
    cellInventory[itemType] = Math.max(0, parseInt(value) || 0);
    newEditingInventories.set(cellKey, cellInventory);
    setEditingInventories(newEditingInventories);
  };


  const itemTypes = ['diamond', 'gold', 'apple', 'emerald', 'redstone'];
  const itemIcons = {
    diamond: '💎',
    gold: '🥇',
    apple: '🍎',
    emerald: '💚',
    redstone: '🔴'
  };

  return (
    <div className="inventory-side-panel">
      <h3>Cell Inventories</h3>
      {selectedCells.size === 0 ? (
        <div className="no-selection-message">
          <p>Select cells from the grid to view and edit their inventories.</p>
          <div className="inventory-preview">
            <h4>Available Items:</h4>
            <div className="preview-items">
              {itemTypes.map(itemType => (
                <div key={itemType} className="preview-item">
                  <span className="item-icon">{itemIcons[itemType]}</span>
                  <span className="item-name">{itemType}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="inventory-cells">
            {Array.from(selectedCells).map(cellKey => {
              const [row, col] = cellKey.split('-');
              const cellInventory = editingInventories.get(cellKey) || {};
              
              return (
                <div key={cellKey} className="inventory-cell">
                  <h4>Cell ({row}, {col})</h4>
                  <div className="inventory-items">
                    {itemTypes.map(itemType => (
                      <div key={itemType} className="inventory-item">
                        <label className="item-label">
                          <span className="item-icon">{itemIcons[itemType]}</span>
                          <span className="item-name">{itemType}</span>
                        </label>
                        <input
                          type="number"
                          min="0"
                          value={cellInventory[itemType] || 0}
                          onChange={(e) => handleInventoryChange(cellKey, itemType, e.target.value)}
                          className="inventory-input"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};

export default InventorySidePanel;
