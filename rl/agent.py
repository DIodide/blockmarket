import torch
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import os
import logging
from collections import defaultdict

try:
    from .network import TradingNetwork
except ImportError:
    from network import TradingNetwork


logger = logging.getLogger(__name__)


class TradingAgent:
    def __init__(self, agent_id, config, items_list, desired_item, initial_inventory=None):
        """
        Initialize a trading agent.
        
        Args:
            agent_id: Unique identifier for this agent
            config: Configuration dictionary
            items_list: List of all possible items in the environment
            desired_item: The item this agent wants to maximize
            initial_inventory: Dict of initial item quantities (optional)
        """
        self.agent_id = agent_id
        self.config = config
        self.items_list = items_list
        self.desired_item = desired_item
        self.num_items = len(items_list)
        
        # Initialize inventory
        if initial_inventory is None:
            # Random initial inventory
            self.inventory = {item: np.random.randint(5, 20) for item in items_list}
        else:
            self.inventory = initial_inventory.copy()
        
        # Initialize trading matrix (how much of item j to accept for 1 of item i)
        # Create symmetric matrix where trading_matrix[j,i] = 1/trading_matrix[i,j]
        self.trading_matrix = self._initialize_symmetric_trading_matrix()
        
        # Neural network for updating trading matrix
        self.network = TradingNetwork(config, self.num_items)
        self.optimizer = optim.Adam(self.network.parameters(), lr=config['learning']['learning_rate'])
        
        # Experience tracking
        self.trade_history = []
        self.reward_history = []
        self.position = np.random.uniform(0, config['environment']['world_size'], 2)  # x, y coordinates
        
        # Performance metrics
        self.generation_start_inventory = self.inventory.copy()
        self.successful_trades = 0
        self.attempted_trades = 0
    
    def _initialize_symmetric_trading_matrix(self):
        """
        Initialize a symmetric trading matrix where trading_matrix[j,i] = 1/trading_matrix[i,j].
        This ensures economic consistency: if I trade 1 A for 2 B, then 1 B trades for 0.5 A.
        """
        matrix = np.zeros((self.num_items, self.num_items))
        
        # Fill upper triangular part (including diagonal)
        for i in range(self.num_items):
            for j in range(i, self.num_items):
                if i == j:
                    # Diagonal: trading item for itself
                    matrix[i, j] = 1.0
                else:
                    # Random rate for upper triangle
                    rate = np.random.uniform(0.5, 2.0)
                    matrix[i, j] = rate
                    # Set lower triangle as inverse
                    matrix[j, i] = 1.0 / rate
        
        # Explicit diagonal constraint as final safeguard
        return self._enforce_diagonal_constraint(matrix)
    
    def _enforce_symmetric_property(self, matrix):
        """
        Enforce the symmetric inverse property on a trading matrix.
        Updates the lower triangle to be the inverse of the upper triangle.
        """
        for i in range(self.num_items):
            for j in range(i + 1, self.num_items):
                # Ensure lower triangle is inverse of upper triangle
                if matrix[i, j] > 0:
                    matrix[j, i] = 1.0 / matrix[i, j]
                else:
                    # If upper is zero, set both to a default rate
                    matrix[i, j] = 1.0
                    matrix[j, i] = 1.0
            
            # Ensure diagonal is 1.0
            matrix[i, i] = 1.0
        
        # Final explicit diagonal constraint
        return self._enforce_diagonal_constraint(matrix)
    
    def _enforce_diagonal_constraint(self, matrix):
        """
        Explicitly ensure diagonal elements are always 1.0.
        This represents trading an item for itself (1:1 ratio).
        """
        np.fill_diagonal(matrix, 1.0)
        return matrix
    
    def get_state_vector(self, market_data=None):
        """Create state vector for neural network input."""
        state_components = []
        
        # Current inventory (normalized)
        inventory_vector = [self.inventory[item] for item in self.items_list]
        max_inventory = max(inventory_vector) if max(inventory_vector) > 0 else 1
        normalized_inventory = [x / max_inventory for x in inventory_vector]
        state_components.extend(normalized_inventory)
        
        # Desired item index (one-hot encoding)
        desired_item_vector = [0.0] * self.num_items
        if self.desired_item in self.items_list:
            desired_item_vector[self.items_list.index(self.desired_item)] = 1.0
        state_components.extend(desired_item_vector)
        
        # Current trading matrix (flattened)
        state_components.extend(self.trading_matrix.flatten())
        
        # Market information (if available)
        if market_data:
            # Average market rates for each item pair
            market_rates = np.zeros((self.num_items, self.num_items))
            for other_agent_id, other_matrix in market_data.items():
                if other_agent_id != self.agent_id:
                    market_rates += other_matrix
            
            if len(market_data) > 1:
                market_rates /= (len(market_data) - 1)  # Exclude self
            
            state_components.extend(market_rates.flatten())
        else:
            # If no market data, pad with zeros
            state_components.extend([0.0] * (self.num_items * self.num_items))
        
        # Recent performance metrics
        recent_success_rate = (self.successful_trades / max(self.attempted_trades, 1))
        state_components.append(recent_success_rate)
        
        return torch.FloatTensor(state_components)
    
    def update_trading_matrix(self, market_data=None):
        """Update trading matrix using neural network."""
        state = self.get_state_vector(market_data)
        
        # Get new trading matrix from network
        with torch.no_grad():
            matrix_update = self.network(state.unsqueeze(0))
            matrix_update = matrix_update.squeeze(0).numpy()
        
        # Reshape to matrix form
        matrix_update = matrix_update.reshape(self.num_items, self.num_items)
        
        # Apply update with learning rate
        learning_rate = self.config['learning']['matrix_update_rate']
        updated_matrix = (1 - learning_rate) * self.trading_matrix + learning_rate * matrix_update
        
        # Ensure positive values and reasonable bounds
        updated_matrix = np.maximum(updated_matrix, 0.1)  # Minimum rate
        updated_matrix = np.minimum(updated_matrix, 10.0)  # Maximum rate
        
        # Enforce symmetric inverse property: trading_matrix[j,i] = 1/trading_matrix[i,j]
        self.trading_matrix = self._enforce_symmetric_property(updated_matrix)
        
        # Explicit diagonal constraint as final safeguard
        self.trading_matrix = self._enforce_diagonal_constraint(self.trading_matrix)
    
    def select_trade_action(self, market_data, other_agents_positions):
        """
        Select trading action based on current state and market conditions.
        
        Returns:
            Tuple (target_agent_id, item_giving, item_wanting, amount_wanting) or None if no trade
            Format: (b_j, D_i, D_j, D_j_amt)
        """
        if not market_data or len(market_data) <= 1:
            return None
        
        best_trade = None
        best_value = -float('inf')
    
        # Evaluate potential trades with each other agent
        for other_agent_id, other_matrix in market_data.items():
            if other_agent_id == self.agent_id:
                continue
            
            # Calculate distance to other agent
            if other_agent_id in other_agents_positions:
                other_pos = other_agents_positions[other_agent_id]
                distance = np.linalg.norm(np.array(self.position) - np.array(other_pos))
            else:
                distance = float('inf')
            
            # Skip if too far away
            if distance > self.config['environment']['max_trade_distance']:
                continue
            
            # Evaluate each possible item to trade for (D_j - what we want)
            for want_item_idx, want_item in enumerate(self.items_list):
                if want_item != self.desired_item:
                    continue  # Only trade for desired item for now
                
                # Find what we can offer that they want (D_i - what we give)
                for give_item_idx, give_item in enumerate(self.items_list):
                    if self.inventory[give_item] <= 0:
                        continue  # Can't trade what we don't have
                    
                    # How much they want for our item (their trading matrix)
                    their_rate = other_matrix[give_item_idx, want_item_idx]
                    if their_rate <= 0:
                        continue  # They don't want this trade
                    
                    # Calculate how much we want to get
                    max_trade_amount = min(
                        self.config['environment']['max_trade_amount'],
                        self.inventory[give_item] * their_rate  # Max we can get based on what we have
                    )
                    
                    if max_trade_amount <= 0:
                        continue
                    
                    # Calculate trade value
                    distance_penalty = 1.0 / (1.0 + distance)
                    trade_value = their_rate * distance_penalty
                    
                    # Prefer trades that get us more of our desired item
                    if want_item == self.desired_item:
                        trade_value *= 2.0  # Bonus for desired item
                    
                    if trade_value > best_value:
                        best_value = trade_value
                        # Amount we want to receive (D_j_amt)
                        desired_amount = min(max_trade_amount, 
                                           self.config['environment']['max_trade_amount'])
                        best_trade = (other_agent_id, give_item, want_item, desired_amount)
        
        return best_trade
    
    def calculate_reward(self, market_data=None):
        """
        Calculate reward based on current state and market opportunities.
        
        Args:
            market_data: Dictionary of other agents' trading matrices
            
        Returns:
            Total reward considering direct value and indirect trading opportunities
        """
        # Primary reward: quantity of desired item
        # primary_reward = self.inventory[self.desired_item]
        primary_reward = 0.0
        
        # Bonus for improvement over generation start
        improvement_bonus = (self.inventory[self.desired_item] - 
                           self.generation_start_inventory[self.desired_item])

        # Laziness penalty        
        # laziness_penalty = -2.0 if self.inventory[self.desired_item] == self.generation_start_inventory[self.desired_item] else 0.0
        laziness_penalty = 0.0

        # Penalty for having zero of desired item
        zero_penalty = -10.0 if self.inventory[self.desired_item] == 0 else 0.0
        
        # Small bonus for successful trades (encourages activity)
        trade_bonus = self.successful_trades * 0.1
        # trade_bonus = 0.0
        
        # NEW: Strategic value based on trading opportunities
        strategic_value = self._calculate_strategic_value(market_data) if market_data else 0.0
        
        total_reward = primary_reward + improvement_bonus + zero_penalty + trade_bonus + strategic_value + laziness_penalty;
        return total_reward
    
    def _calculate_strategic_value(self, market_data):
        """
        Calculate strategic value of current inventory considering indirect trading paths.
        
        This function evaluates how valuable each item in the inventory is as a means
        to eventually obtain the desired item through multi-hop trades.
        
        Args:
            market_data: Dictionary of other agents' trading matrices
            
        Returns:
            Strategic value score
        """
        if not market_data or len(market_data) <= 1:
            return 0.0
        
        desired_item_idx = self.items_list.index(self.desired_item)
        strategic_value = 0.0
        
        # For each item in our inventory, calculate its strategic value
        for item_idx, item in enumerate(self.items_list):
            if item == self.desired_item:
                continue  # Already counted in primary reward
                
            item_quantity = self.inventory[item]
            if item_quantity <= 0:
                continue
            
            # Calculate the best conversion rate from this item to desired item
            # considering both direct and indirect paths
            best_conversion_rate = self._find_best_conversion_path(
                item_idx, desired_item_idx, market_data, max_hops=3
            )
            
            # Strategic value = quantity * best_conversion_rate * discount_factor
            # Discount factor reduces value of indirect paths
            discount_factor = 0.3  # Weight for strategic vs direct value
            item_strategic_value = item_quantity * best_conversion_rate * discount_factor
            strategic_value += item_strategic_value
        
        return strategic_value
    
    def _find_best_conversion_path(self, from_item_idx, to_item_idx, market_data, max_hops=3):
        """
        Find the best conversion rate from one item to another through trading paths.
        
        Uses a breadth-first search with dynamic programming to find optimal paths.
        
        Args:
            from_item_idx: Index of starting item
            to_item_idx: Index of target item
            market_data: Dictionary of other agents' trading matrices
            max_hops: Maximum number of trading hops to consider
            
        Returns:
            Best conversion rate (how much of to_item we can get per unit of from_item)
        """
        if from_item_idx == to_item_idx:
            return 1.0
        
        # Dynamic programming table: best_rate[item_idx][hops] = best rate to get to_item
        best_rates = {}
        
        # Initialize: direct trades (1 hop)
        best_rates[from_item_idx] = {0: 1.0}  # We start with 1 unit of from_item
        
        for hop in range(1, max_hops + 1):
            new_rates = {}
            
            # For each item we can currently reach
            for current_item_idx in best_rates:
                if hop - 1 not in best_rates[current_item_idx]:
                    continue
                    
                current_rate = best_rates[current_item_idx][hop - 1]
                if current_rate <= 0:
                    continue
                
                # Try trading with each other agent
                for agent_id, other_matrix in market_data.items():
                    if agent_id == self.agent_id:
                        continue
                    
                    # Check all possible items we can get from this agent
                    for target_item_idx in range(len(self.items_list)):
                        if target_item_idx == current_item_idx:
                            continue
                        
                        # Rate: how much of target_item we get for 1 unit of current_item
                        trade_rate = other_matrix[current_item_idx, target_item_idx]
                        if trade_rate <= 0:
                            continue
                        
                        # Total rate through this path
                        total_rate = current_rate * trade_rate
                        
                        # Update best rate for target_item at this hop count
                        if target_item_idx not in new_rates:
                            new_rates[target_item_idx] = {}
                        
                        if hop not in new_rates[target_item_idx]:
                            new_rates[target_item_idx][hop] = total_rate
                        else:
                            new_rates[target_item_idx][hop] = max(
                                new_rates[target_item_idx][hop], total_rate
                            )
            
            # Merge new rates into best_rates
            for item_idx, hop_rates in new_rates.items():
                if item_idx not in best_rates:
                    best_rates[item_idx] = {}
                best_rates[item_idx].update(hop_rates)
        
        # Find the best rate to reach to_item_idx across all hop counts
        if to_item_idx not in best_rates:
            return 0.0
        
        best_rate = 0.0
        for hop in range(1, max_hops + 1):
            if hop in best_rates[to_item_idx]:
                # Apply diminishing returns for longer paths
                hop_penalty = 0.9 ** (hop - 1)  # Each additional hop reduces value
                adjusted_rate = best_rates[to_item_idx][hop] * hop_penalty
                best_rate = max(best_rate, adjusted_rate)
        
        return best_rate
    
    def update_policy(self, reward):
        """Update the agent's policy based on reward."""
        self.reward_history.append(reward)
        
        # Simple policy gradient update
        if len(self.reward_history) >= 2:
            # Calculate advantage (reward improvement)
            advantage = reward - self.reward_history[-2]
            
            # Update network if we have enough experience
            if len(self.trade_history) > 0:
                # Use last state and action for update
                last_state = self.get_state_vector()
                
                # Create target (current trading matrix + advantage signal)
                target = torch.FloatTensor(self.trading_matrix.flatten())
                if advantage > 0:
                    target *= 1.01  # Slight increase if positive advantage
                else:
                    target *= 0.99  # Slight decrease if negative advantage
                
                # Forward pass
                predicted = self.network(last_state.unsqueeze(0))
                
                # Calculate loss
                loss = F.mse_loss(predicted, target.unsqueeze(0))
                
                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
    
    def execute_trade(self, trade_partner_id, item_given, amount_given, item_received, amount_received):
        """Execute a trade transaction."""
        # Update inventory
        self.inventory[item_given] -= amount_given
        self.inventory[item_received] += amount_received
        
        # Ensure non-negative inventory
        self.inventory[item_given] = max(0, self.inventory[item_given])
        
        # Record trade
        trade_record = {
            'partner': trade_partner_id,
            'given': (item_given, amount_given),
            'received': (item_received, amount_received),
            'timestep': len(self.trade_history)
        }
        self.trade_history.append(trade_record)
        self.successful_trades += 1
        
        logger.debug(f"Agent {self.agent_id} traded {amount_given} {item_given} for {amount_received} {item_received}")
    
    def reset_for_new_generation(self):
        """Reset agent state for a new generation."""
        self.generation_start_inventory = self.inventory.copy()
        self.successful_trades = 0
        self.attempted_trades = 0
        self.trade_history = []
        # Keep reward history for learning
    
    def get_fitness(self, market_data=None):
        """Calculate fitness score for genetic algorithm selection."""
        return self.calculate_reward(market_data)
    
    def mutate(self, mutation_rate=0.1):
        """Apply mutation to the agent's parameters."""
        if np.random.random() < mutation_rate:
            # Mutate neural network weights
            with torch.no_grad():
                for param in self.network.parameters():
                    noise = torch.randn_like(param) * 0.01
                    param.add_(noise)
        
        # Mutate trading matrix while preserving symmetric property
        if np.random.random() < mutation_rate:
            # Add small noise to upper triangle only
            for i in range(self.num_items):
                for j in range(i + 1, self.num_items):  # Upper triangle only
                    noise = np.random.normal(0, 0.05)  # Small mutation
                    self.trading_matrix[i, j] += noise
                    # Clamp to reasonable bounds
                    self.trading_matrix[i, j] = np.clip(self.trading_matrix[i, j], 0.1, 10.0)
            
            # Enforce symmetric property after mutation
            self.trading_matrix = self._enforce_symmetric_property(self.trading_matrix)
            
            # Explicit diagonal constraint as final safeguard
            self.trading_matrix = self._enforce_diagonal_constraint(self.trading_matrix)
        
        # Mutate position slightly
        position_noise = np.random.normal(0, 1.0, 2)
        self.position += position_noise
        
        # Keep position within bounds
        world_size = self.config['environment']['world_size']
        self.position = np.clip(self.position, 0, world_size)
    
    def save_model(self, filepath):
        """Save agent's neural network state."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            checkpoint = {
                'network_state_dict': self.network.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'agent_id': self.agent_id,
                'desired_item': self.desired_item,
                'inventory': self.inventory,
                'trading_matrix': self.trading_matrix,
                'position': self.position,
                'reward_history': self.reward_history
            }
            torch.save(checkpoint, filepath)
            logger.info(f"Agent {self.agent_id} model saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save agent {self.agent_id} model: {e}")
    
    def load_model(self, filepath):
        """Load agent's neural network state."""
        if os.path.exists(filepath):
            try:
                checkpoint = torch.load(filepath, map_location='cpu', weights_only=False)
                self.network.load_state_dict(checkpoint['network_state_dict'])
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                self.inventory = checkpoint.get('inventory', self.inventory)
                self.trading_matrix = checkpoint.get('trading_matrix', self.trading_matrix)
                self.position = checkpoint.get('position', self.position)
                self.reward_history = checkpoint.get('reward_history', [])
                logger.info(f"Agent {self.agent_id} model loaded from {filepath}")
                return True
            except Exception as e:
                logger.error(f"Failed to load agent {self.agent_id} model: {e}")
                return False
        return False