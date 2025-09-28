## Features

- 🤖 **Multi-Bot Management**: Spawn and manage multiple Minecraft bots simultaneously
- 🎮 **Creative Mode Operations**: Full creative mode support with inventory management and flying
- 🗺️ **Grid-Based Spawning**: Bots spawn in a configurable 2D grid layout
- 💱 **Trading Animations**: Animated bot-to-bot trading with particle effects and movements
- 🔄 **Real-Time Communication**: Socket.IO integration for receiving commands from external servers
- 📦 **Queue System**: Trade queue management for handling high-frequency trade commands
- 🎨 **Visual Effects**: Particle effects, jumping animations, and celebration sequences

## Project Structure

```
bm-mineflayer-controller/
├── src/
│   └── sim.js                    # Core simulation class with bot management
├── socketRecieve.js              # Socket.IO client with queue system
├── socketRecieveNoQueue.js       # Socket.IO client without queue (simplified)
├── simulationClass.js            # Wrapper class for trade processing
├── example.js                    # Basic usage example
├── simulationClassExample.js     # Simulation class usage example
├── test.js                       # Test file
└── package.json                  # Dependencies and scripts
```

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd bm-mineflayer-controller
```

2. **Install dependencies**:
```bash
npm install
```

3. **Verify Node.js version** (recommended: Node.js 18 or 20):
```bash
node --version
```

## Dependencies

- **mineflayer**: ^4.33.0 - Minecraft bot framework
- **mineflayer-pathfinder**: ^2.4.5 - Pathfinding for bot movement
- **minecraft-data**: ^3.98.0 - Minecraft game data
- **vec3**: ^0.1.10 - 3D vector operations
- **socket.io-client**: ^4.8.1 - Real-time communication

## Quick Start

### Basic Simulation

```javascript
const { Sim } = require('./src/sim');

const config = {
  host: 'localhost',
  port: 25565,
  version: '1.20.6',
  auth: 'offline',
  usernames: ['Bot1', 'Bot2', 'Bot3'],
  grid: [
    [1, 0, 1],
    [0, 1, 0],
    [1, 0, 1]
  ],
  base: { x: 0, y: 100, z: 0 },
  spacing: 4
};

const sim = new Sim(config);
await sim.spawnFromGrid();

// Execute a trade between bots
await sim.trade('Bot1', 'diamond_sword', 'Bot2', 'emerald');
```

### Socket.IO Integration

```javascript
const { SimulationSocketClient } = require('./socketRecieve');

const client = new SimulationSocketClient();
client.connect('http://localhost:3000');
```

## Core Classes

### Sim Class (`src/sim.js`)

The main simulation class that manages bot creation, movement, and trading.

**Key Methods:**
- `spawnFromGrid()`: Spawns bots according to the grid configuration
- `trade(bot1, item1, bot2, item2)`: Executes animated trading between two bots
- `setBotInventory(botName, items)`: Sets a bot's inventory using creative mode commands
- `botsGatherAndCelebrate(count)`: Makes bots gather and perform celebration animations

**Configuration:**
```javascript
{
  host: string,           // Minecraft server host
  port: number,           // Minecraft server port
  version?: string,       // Minecraft version (default: '1.20.6')
  auth?: string,          // Authentication type ('offline' or 'microsoft')
  usernames: string[],    // Array of bot usernames
  grid: (0|1)[][],        // 2D grid where 1 = spawn bot
  base: {x, y, z},        // World origin for grid
  spacing?: number        // Blocks between grid cells (default: 4)
}
```

### SimulationSocketClient Class (`socketRecieve.js`)

Handles real-time communication with external servers via Socket.IO.

**Key Features:**
- **Persistent Connection**: Automatic reconnection with exponential backoff
- **Trade Queue System**: Buffers incoming trade commands for consistent processing
- **Grid Parsing**: Converts `botInventoryMap` data into grid and inventory configurations
- **Status Updates**: Sends real-time status updates to the server

**Events:**
- `startSimulation`: Receives simulation configuration and starts bots
- `stopSimulation`: Stops current simulation and disconnects bots
- `trade`: Receives trade commands and adds them to the processing queue
- `getStatus`: Responds with current simulation status

### SimulationClass (`simulationClass.js`)

Wrapper class that provides a simplified interface for trade processing.

**Key Methods:**
- `trade_timestep(items)`: Processes an array of items by pairing them and executing trades

## Usage Examples

### 1. Basic Bot Spawning

```javascript
const { Sim } = require('./src/sim');

const config = {
  host: 'mcpanel.blockwarriors.ai',
  port: 25565,
  usernames: ['Bot1', 'Bot2', 'Bot3', 'Bot4'],
  grid: [
    [1, 0, 1, 0],
    [0, 1, 0, 1]
  ],
  base: { x: -13.5, y: -60, z: -13.5 },
  spacing: 3
};

const sim = new Sim(config);
await sim.spawnFromGrid();
```

### 2. Trading Animation

```javascript
// Execute a trade with visual effects
await sim.trade('Bot1', 'diamond_sword', 'Bot2', 'emerald');

// Make all bots celebrate
await sim.botsGatherAndCelebrate(4);
```

### 3. Socket.IO Server Integration

```javascript
const { SimulationSocketClient } = require('./socketRecieve');

const client = new SimulationSocketClient();

// Connect to your server
client.connect('http://your-server.com:3000');

// The client will automatically handle:
// - startSimulation events
// - trade commands
// - status requests
```

### 4. Custom Inventory Setup

```javascript
const items = [
  { item: 'diamond_sword', count: 1 },
  { item: 'emerald', count: 5 },
  { item: 'apple', count: 10 }
];

await sim.setBotInventory('Bot1', items);
```

## Configuration

### Grid Layout

The grid is a 2D array where:
- `0` = empty cell
- `1` = spawn a bot at this position

```javascript
grid: [
  [1, 0, 1, 0],  // Row 0: Bot1 at (0,0), Bot2 at (0,2)
  [0, 1, 0, 1],  // Row 1: Bot3 at (1,1), Bot4 at (1,3)
  [1, 1, 0, 0]   // Row 2: Bot5 at (2,0), Bot6 at (2,1)
]
```

### Bot Inventory Map

When using Socket.IO, the server sends a `botInventoryMap` that maps grid positions to inventory data:

```javascript
botInventoryMap: {
  '1-0': { diamond: 0, gold: 0, apple: 0, emerald: 0, redstone: 0 },
  '1-3': { diamond: 2, gold: 0, apple: 5, emerald: 1, redstone: 0 },
  '2-7': { diamond: 0, gold: 3, apple: 0, emerald: 0, redstone: 10 }
}
```


## API Reference

### Sim Class Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `spawnFromGrid()` | None | Spawns bots according to grid configuration |
| `trade(bot1, item1, bot2, item2)` | bot1: string, item1: string, bot2: string, item2: string | Executes animated trade between two bots |
| `setBotInventory(botName, items)` | botName: string, items: Array | Sets bot inventory using creative commands |
| `botsGatherAndCelebrate(count)` | count: number | Makes bots gather and celebrate |
| `goto(bot, pos)` | bot: Bot, pos: Vec3 | Moves bot to position with pathfinding |

### Socket Events

| Event | Data | Description |
|-------|------|-------------|
| `startSimulation` | `{botInventoryMap, host, port, version, auth, base, spacing}` | Starts new simulation |
| `stopSimulation` | None | Stops current simulation |
| `trade` | `{tradeData: {trades: Array}}` | Adds trades to processing queue |
| `getStatus` | None | Requests current status |


## License

This project is part of the BlockMarket ecosystem. Please refer to the main project license for usage terms.