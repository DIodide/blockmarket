# Testing Trade Emission

## Issue Fixed

I found and fixed a critical bug in `agent.py` line 645 where the trading matrix diagonal was being set to 0.0 instead of 1.0 during mutation, which would prevent same-item trades.

## Quick Test

To test if trades are now being emitted:

### Option 1: Run Debug Script

```bash
cd rl
python debug_trades.py
```

This will:
- Create 3 agents with diverse inventories
- Run a short simulation 
- Show detailed debug output
- Log everything to `debug_trades.log`

### Option 2: Run Unified Mode with Debug

```bash
cd rl
python main.py --mode unified --debug --no-training
```

Then in another terminal, connect to the Socket.IO server and send a start_simulation command.

### Option 3: Run Socket-Only Mode

```bash
cd rl
python main.py --mode socket-only --debug
```

## What to Look For

In the debug output, you should see:

1. **Agent Creation**: 
   ```
   Created agent agent_0-0: inventory={...}, desired=diamond
   Agent trading matrix: [[...]]
   ```

2. **Trade Requests**:
   ```
   Agent agent_0-0 trade action: ('agent_1-1', 'gold', 'diamond', 2.5)
   Valid trade request: agent_0-0 -> agent_1-1, gold for diamond
   Collected 2 valid trade requests from 3 agents
   ```

3. **Trade Execution**:
   ```
   Trade executed: agent_0-0 gave 1.25 gold for 2.5 diamond from agent_1-1
   ```

4. **Trade Emission**:
   ```
   Emitted trade data for timestep 5: 1 trades
   ```

## Expected Socket Emission Format

When trades occur, you should see emissions like:

```json
{
  "timestep": 5,
  "generation": 0,
  "trades_count": 1,
  "trades": [
    {
      "requester_id": "agent_0-0",
      "target_id": "agent_1-1", 
      "item_given": "gold",
      "amount_given": 1.25,
      "item_received": "diamond",
      "amount_received": 2.5,
      "requester_cell": "0-0",
      "target_cell": "1-1"
    }
  ]
}
```

## Common Issues

1. **No Trades Generated**: Check if agents have diverse inventories and different desired items
2. **Distance Issues**: Agents might be too far apart (check `max_trade_distance` in config)
3. **Trading Matrix Issues**: Check if trading matrix values are reasonable (0.1 to 10.0 range)
4. **Socket Connection**: Make sure Socket.IO server is running and accessible

## Configuration

Key config values that affect trading:
- `max_trade_distance: 20.0` - Maximum distance for trades
- `max_trade_amount: 5.0` - Maximum amount per trade  
- `population_size: 5` - Number of agents
- `generation_length: 100` - Timesteps per generation

## Debugging

For maximum debug output, set in `config.yaml`:
```yaml
logging:
  level: 'DEBUG'
```

Or use the `--debug` flag when running.
