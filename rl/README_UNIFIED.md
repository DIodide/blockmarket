# Unified Multi-Agent Trading Environment

This system now supports running both the Flask web visualization and Socket.IO client functionality simultaneously, allowing you to:

1. **Visualize** the trading environment through a web interface
2. **Control** the environment externally via Socket.IO events
3. **Run** internal training loops independently

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Update `config.yaml` to configure socket settings:

```yaml
socket:
  enabled: true  # Enable socket client functionality
  server_url: 'http://localhost:3001'  # Socket.IO server URL
  namespace: '/model'  # Namespace to connect to
  auto_connect: true  # Automatically connect on startup
```

## Running Modes

### 1. Unified Mode (Default) - Recommended

Runs Flask web server + Socket.IO client + internal training simultaneously:

```bash
python main.py --mode unified
# or simply
python main.py
```

**Features:**
- ✅ Web visualization at `http://localhost:8080`
- ✅ Socket.IO client listening for external `start_simulation` events
- ✅ Internal training loop running in background
- ✅ All components running in separate threads

**Options:**
```bash
python main.py --mode unified --no-web      # Disable web interface
python main.py --mode unified --no-training # Disable internal training
python main.py --mode unified --no-socket   # Disable socket client
```

### 2. Training Mode

Original training-only mode with optional web visualization:

```bash
python main.py --mode training
```

### 3. Socket-Only Mode

Only runs the Socket.IO client (no web interface, no training):

```bash
python main.py --mode socket-only
```

## Usage with External Systems

### Starting External Simulations

When running in unified mode, the system listens for `start_simulation` events on the configured Socket.IO namespace. Send data in this format:

```json
{
  "botInventoryMap": {
    "0-0": {"diamond": 5, "gold": 10, "apple": 3, "emerald": 2, "redstone": 8},
    "1-2": {"diamond": 3, "gold": 8, "apple": 5, "emerald": 4, "redstone": 6}
  }
}
```

### Receiving Trade Data

The system emits `trade` events with this format:

```json
{
  "timestep": 42,
  "generation": 0,
  "trades_count": 2,
  "trades": [
    {
      "requester_id": "agent_0-0",
      "target_id": "agent_1-2",
      "item_given": "gold",
      "amount_given": 2.5,
      "item_received": "diamond", 
      "amount_received": 1.0,
      "requester_cell": "0-0",
      "target_cell": "1-2"
    }
  ]
}
```

## Architecture

```
┌─────────────────────────────────────────┐
│           Unified Trading App           │
├─────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────────────┐ │
│  │    Flask    │ │    Socket.IO        │ │
│  │ Web Server  │ │     Client          │ │
│  │             │ │                     │ │
│  │ Port: 8080  │ │ External Commands   │ │
│  └─────────────┘ └─────────────────────┘ │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │      Internal Training Loop        │ │
│  │   (Genetic Algorithm + RL)         │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │     External Simulation Loop       │ │
│  │  (Triggered by Socket Events)      │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Key Features

1. **Dual Simulation Support**: Run both internal training and external socket-controlled simulations
2. **Real-time Web Visualization**: Monitor all trading activity through the web interface
3. **Thread-Safe**: All components run in separate threads with proper synchronization
4. **Flexible Configuration**: Enable/disable components as needed
5. **Backward Compatibility**: Original training mode still available

## Example Integration

```python
# External system sending start_simulation
import socketio

sio = socketio.Client()
sio.connect('http://localhost:3001')

# Start external simulation
sio.emit('start_simulation', {
    'botInventoryMap': {
        '5-10': {'diamond': 3, 'gold': 7, 'apple': 12, 'emerald': 0, 'redstone': 5},
        '7-2': {'diamond': 0, 'gold': 2, 'apple': 8, 'emerald': 1, 'redstone': 0}
    }
}, namespace='/model')

# Listen for trade events
@sio.event(namespace='/model')
def trade(data):
    print(f"Trade received: {data}")
```

## Convenience Script

Use the convenience script for easier launching:

```bash
python run.py --mode unified
python run.py --mode training --no-web
python run.py --mode socket-only --debug
```
