# Multi-Agent Trading Environment

A reinforcement learning environment where agents learn to trade items with each other using neural networks and genetic algorithms.

## Overview

This system implements a multi-agent trading environment where:

- **Agents** have inventories of different items and want to maximize specific items
- **Trading matrices** determine exchange rates between items for each agent
- **Neural networks** learn to update trading matrices based on market conditions
- **Genetic algorithms** evolve the population over generations
- **Distance-based trading** creates spatial dynamics in the trading world

## Key Features

### 🤖 Intelligent Agents
- Each agent has a neural network that learns optimal trading strategies
- Agents update their trading matrices every timestep based on:
  - Current inventory state
  - Market conditions (other agents' trading matrices)
  - Recent trading success
  - Spatial position in the world

### 🧬 Genetic Evolution
- Population evolves over generations
- Bottom 50% of agents are eliminated each generation
- Top performers reproduce with mutation
- Fitness based on quantity of desired items

### 🌍 Spatial Trading
- Agents have positions in a 2D world
- Trade probability decreases with distance
- Agents can move and mutate their positions

### 📊 Real-time Visualization
- Web-based interface showing live trading dynamics
- Agent positions, fitness distributions, and trade networks
- Generation history and performance metrics

## Architecture

### Core Components

1. **`agent.py`** - TradingAgent class with neural network-based decision making
2. **`environment.py`** - TradingEnvironment managing multi-agent interactions
3. **`network.py`** - Neural network architectures for trading matrix prediction
4. **`training.py`** - Training loop with per-timestep updates and genetic selection
5. **`web_server.py`** - Flask-based visualization interface
6. **`utils.py`** - Utility functions for analysis and logging
7. **`config.py`** - Configuration management

### Key Differences from Cart-Pole PPO

- **Per-timestep updates** instead of batch updates every 200 steps
- **Genetic algorithm** instead of pure reinforcement learning
- **Multi-agent environment** with agent-agent interactions
- **Spatial dynamics** with distance-based trade probabilities
- **Trading matrices** as the primary learned policy

## Usage

### Installation

```bash
cd blockmarket/rl
pip install -r requirements.txt
```

### Running the Environment

```bash
# Run with web interface (default) - RECOMMENDED
python run.py

# Alternative: Run main directly (may have import issues)
python main.py

# Run without web interface
python run.py --no-web

# Run with debug logging
python run.py --debug

# Use custom config file
python run.py --config my_config.yaml

# Demonstrate strategic value function
python example_strategic_value.py

# Demonstrate new trade request format
python example_trade_format.py
```

### Web Interface

Once running, visit `http://localhost:8080` to see:
- Live agent positions and trading activity
- Fitness distributions and top performers
- Generation history and statistics
- Recent trade transactions

## Configuration

Edit `config.yaml` to customize:

```yaml
environment:
  world_size: 100.0          # Size of 2D trading world
  max_trade_distance: 20.0   # Maximum distance for trades
  items_list: ['wood', 'stone', 'iron', 'gold', 'food']
  population_size: 50        # Number of agents
  generation_length: 100     # Timesteps per generation
  survival_rate: 0.5         # Fraction surviving each generation

network:
  hidden_dim: 128           # Neural network hidden layer size

learning:
  learning_rate: 0.001      # Neural network learning rate
  matrix_update_rate: 0.1   # Trading matrix update rate

training:
  max_generations: 100      # Maximum generations to run
  target_fitness: 100.0     # Target fitness to stop training
```

## Trading Mechanics

### Trading Matrix
Each agent maintains an `N×N` matrix where `A[i,j]` represents how much of item `j` the agent will accept for 1 unit of item `i`.

### Trade Process (Per Timestep)
1. **Matrix Update**: Agents update trading matrices using neural networks
2. **Market Publication**: All trading matrices become publicly visible
3. **Action Selection**: Agents generate trade requests in format `(b_i, b_j, D_i, D_j, D_j_amt)`
   - `b_i`: Requester agent ID
   - `b_j`: Target agent ID  
   - `D_i`: Item the requester is offering
   - `D_j`: Item the requester wants
   - `D_j_amt`: Amount of D_j desired
4. **Request Validation**: Invalid requests (insufficient resources) are filtered out
5. **Conflict Resolution**: Distance-based probability resolves competing trades
6. **Trade Execution**: Valid trades are executed, inventories updated
7. **Policy Update**: Agents update neural networks based on rewards

### Genetic Algorithm (Per Generation)
1. **Fitness Evaluation**: Based on quantity of desired items
2. **Selection**: Top 50% survive to next generation
3. **Reproduction**: Survivors create offspring with mutations
4. **Population Reset**: New generation begins fresh trading

## Suggested Improvements

### Trading Matrix Updates
- **Market-responsive rates**: Adjust based on supply/demand
- **Momentum-based learning**: Use moving averages of successful rates
- **Multi-objective optimization**: Balance multiple items, not just one

### Value Functions

The system implements a sophisticated **Strategic Value Function** that goes beyond simple quantity maximization:

- **Primary Value**: Direct quantity of desired item
- **Strategic Value**: Considers indirect trading paths through multi-hop trades  
- **Path Optimization**: Uses dynamic programming to find optimal conversion routes
- **Market Awareness**: Evaluates opportunities based on all agents' trading matrices

**Key Innovation**: Instead of just valuing the desired item, agents now value intermediate items based on their potential to eventually acquire more of the desired item through optimal trading chains.

**Example**: An agent wanting gold will value iron not just for direct gold trades, but also for indirect paths like iron → wood → gold if that yields better overall conversion rates.

### Advanced Features
- **Communication**: Allow agents to signal intentions
- **Reputation systems**: Track trading partner reliability
- **Dynamic items**: Items that expire or transform over time
- **Market makers**: Special agents that provide liquidity

## Example Output

```
🏪 Multi-Agent Trading Environment Starting
Population size: 50
Items: ['wood', 'stone', 'iron', 'gold', 'food']
🌐 Web interface available at http://localhost:8080

Generation 0 completed in 12.34s
Best fitness: 45.20
Average fitness: 23.10
Total trades: 1,247

🎉 New best fitness achieved: 67.80
Generation 5 completed in 11.89s
```

## File Structure

```
blockmarket/rl/
├── agent.py           # Trading agent implementation
├── environment.py     # Multi-agent environment
├── network.py         # Neural network architectures
├── training.py        # Training loop and genetic algorithm
├── web_server.py      # Visualization web server
├── utils.py           # Utility functions
├── config.py          # Configuration management
├── main.py            # Main entry point
├── config.yaml        # Default configuration
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

This implementation provides a solid foundation for exploring multi-agent trading dynamics with neural networks and genetic algorithms, while maintaining the clean structure and best practices from the cart-pole-ppo reference implementation.

## Troubleshooting

### Import Errors
If you encounter `ImportError: attempted relative import with no known parent package`:
- Use `python run.py` instead of `python main.py`
- Ensure you're running from the `blockmarket/rl/` directory
- Check that all required packages are installed: `pip install -r requirements.txt`

### Web Interface Issues
If the web interface shows errors:
- Check the terminal for detailed error messages
- Ensure Flask is properly installed
- Try restarting the application

### Training Issues
If training shows unexpected fitness values:
- Check that agents have valid initial inventories
- Verify trading matrices are properly initialized
- Monitor the logs for validation errors in trade requests
