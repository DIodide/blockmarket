#!/usr/bin/env node
/**
 * Test Socket.IO server to demonstrate communication with Python client.
 * This simulates the JavaScript side that would send start_simulation commands.
 */

const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Sample bot inventory data
const sampleBotInventoryMap = {
  "0-0": {
    "diamond": 5,
    "gold": 10,
    "apple": 3,
    "emerald": 2,
    "redstone": 8
  },
  "0-1": {
    "diamond": 3,
    "gold": 8,
    "apple": 5,
    "emerald": 4,
    "redstone": 6
  },
  "1-0": {
    "diamond": 7,
    "gold": 6,
    "apple": 4,
    "emerald": 3,
    "redstone": 9
  },
  "1-1": {
    "diamond": 4,
    "gold": 12,
    "apple": 2,
    "emerald": 5,
    "redstone": 7
  }
};

io.on('connection', (socket) => {
  console.log(`Client connected: ${socket.id}`);
  
  // Handle simulation events from Python client
  socket.on('simulation_started', (data) => {
    console.log('Simulation started:', data);
  });
  
  socket.on('simulation_stopped', (data) => {
    console.log('Simulation stopped:', data);
  });
  
  socket.on('simulation_error', (data) => {
    console.error('Simulation error:', data);
  });
  
  socket.on('trade', (data) => {
    console.log(`Trade data received (timestep ${data.timestep}):`, {
      trades_count: data.trades_count,
      generation: data.generation,
      trades: data.trades
    });
    
    // Log individual trades
    if (data.trades && data.trades.length > 0) {
      data.trades.forEach((trade, index) => {
        console.log(`  Trade ${index + 1}: ${trade.requester_cell} (${trade.requester_id}) gave ${trade.amount_given} ${trade.item_given} for ${trade.amount_received} ${trade.item_received} from ${trade.target_cell} (${trade.target_id})`);
      });
    }
  });
  
  socket.on('disconnect', () => {
    console.log(`Client disconnected: ${socket.id}`);
  });
  
  // Send start_simulation command after a short delay
  setTimeout(() => {
    console.log('Sending start_simulation command...');
    socket.emit('start_simulation', {
      botInventoryMap: sampleBotInventoryMap
    });
  }, 2000);
  
  // Send stop command after 30 seconds for testing
  setTimeout(() => {
    console.log('Sending stop_simulation command...');
    socket.emit('stop_simulation');
  }, 30000);
});

// Simple web interface for monitoring
app.get('/', (req, res) => {
  res.send(`
    <html>
      <head><title>Trading Simulation Socket Server</title></head>
      <body>
        <h1>Trading Simulation Socket.IO Server</h1>
        <p>Server running on port 3000</p>
        <p>Connect Python client to: <code>http://localhost:3000</code></p>
        <h2>Sample Bot Inventory Map:</h2>
        <pre>${JSON.stringify(sampleBotInventoryMap, null, 2)}</pre>
        <p>Check console for trade data...</p>
      </body>
    </html>
  `);
});

const PORT = process.env.PORT || 3000;
httpServer.listen(PORT, () => {
  console.log(`Socket.IO server running on http://localhost:${PORT}`);
  console.log('Waiting for Python client connections...');
});
