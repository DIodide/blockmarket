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
    def __init__(
        self, agent_id, config, items_list, desired_item, initial_inventory=None
    ):
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
            self.inventory = {item: np.random.randint(5, 15) for item in items_list}
        else:
            self.inventory = initial_inventory.copy()

        # Initialize trading matrix (how much of item j to accept for 1 of item i)
        self.trading_matrix = np.random.uniform(
            0.5, 2.0, (self.num_items, self.num_items)
        )
        # Diagonal should be 1 (trading item for itself at 1:1 rate)
        np.fill_diagonal(self.trading_matrix, 1.0)

        # Neural network for updating trading matrix
        self.network = TradingNetwork(config, self.num_items)
        self.optimizer = optim.Adam(
            self.network.parameters(), lr=config["learning"]["learning_rate"]
        )

        # Experience tracking
        self.trade_history = []
        self.reward_history = []
        self.position = np.random.uniform(
            0, config["environment"]["world_size"], 2
        )  # x, y coordinates

        # Performance metrics
        self.generation_start_inventory = self.inventory.copy()
        self.successful_trades = 0
        self.attempted_trades = 0

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
                market_rates /= len(market_data) - 1  # Exclude self

            state_components.extend(market_rates.flatten())
        else:
            # If no market data, pad with zeros
            state_components.extend([0.0] * (self.num_items * self.num_items))

        # Recent performance metrics
        recent_success_rate = self.successful_trades / max(self.attempted_trades, 1)
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
        learning_rate = self.config["learning"]["matrix_update_rate"]
        self.trading_matrix = (
            1 - learning_rate
        ) * self.trading_matrix + learning_rate * matrix_update

        # Ensure diagonal is 1
        np.fill_diagonal(self.trading_matrix, 1.0)
        self.trading_matrix = np.maximum(self.trading_matrix, 0.1)  # Minimum rate
        self.trading_matrix = np.minimum(self.trading_matrix, 10.0)  # Maximum rate
        # Re-ensure diagonal stays 1 after min/max operations
        np.fill_diagonal(self.trading_matrix, 1.0)

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
        best_value = -float("inf")

        # Get recent trade partners to avoid immediate cycles
        recent_partners = self._get_recent_trade_partners()

        # Evaluate potential trades with each other agent
        for other_agent_id, other_matrix in market_data.items():
            if other_agent_id == self.agent_id:
                continue

            # Calculate distance to other agent
            if other_agent_id in other_agents_positions:
                other_pos = other_agents_positions[other_agent_id]
                distance = np.linalg.norm(np.array(self.position) - np.array(other_pos))
            else:
                distance = float("inf")

            # Skip if too far away
            if distance > self.config["environment"]["max_trade_distance"]:
                continue

            # Calculate penalty for recent trading with this agent
            cycle_penalty = self._calculate_cycle_penalty(
                other_agent_id, recent_partners
            )

            # Evaluate each possible item to trade for (D_j - what we want)
            for want_item_idx, want_item in enumerate(self.items_list):
                if want_item != self.desired_item:
                    # Check if this item has strategic value for reaching our desired item
                    strategic_value = self._calculate_strategic_value_for_item(
                        want_item, market_data
                    )
                    if strategic_value <= 0:
                        continue  # No strategic value, skip this item

                # Find what we can offer that they want (D_i - what we give)
                for give_item_idx, give_item in enumerate(self.items_list):
                    if self.inventory[give_item] <= 0:
                        continue  # Can't trade what we don't have

                    # Check if this trade would create an immediate cycle
                    if self._would_create_cycle(
                        other_agent_id, give_item, want_item, recent_partners
                    ):
                        continue  # Skip trades that would create cycles

                    # How much they want for our item (their trading matrix)
                    their_rate = other_matrix[give_item_idx, want_item_idx]
                    if their_rate <= 0:
                        continue  # They don't want this trade

                    # Calculate how much we want to get
                    max_trade_amount = min(
                        self.config["environment"]["max_trade_amount"],
                        self.inventory[give_item]
                        * their_rate,  # Max we can get based on what we have
                    )

                    # Set minimum trade threshold to avoid micro-trades
                    min_trade_threshold = 0.01
                    if max_trade_amount <= min_trade_threshold:
                        continue

                    # Calculate trade value
                    distance_penalty = 1.0 / (1.0 + distance)
                    trade_value = their_rate * distance_penalty

                    # Apply cycle penalty to discourage repeated trading with same partner
                    trade_value *= cycle_penalty

                    # Apply bonuses based on item type
                    if want_item == self.desired_item:
                        trade_value *= 2.0  # High bonus for desired item
                    else:
                        # For intermediate items, use strategic value as multiplier
                        strategic_bonus = self._calculate_strategic_value_for_item(
                            want_item, market_data
                        )
                        trade_value *= (
                            1.0 + strategic_bonus
                        )  # Bonus based on strategic value

                    if trade_value > best_value:
                        best_value = trade_value
                        # Amount we want to receive (D_j_amt)
                        desired_amount = min(
                            max_trade_amount,
                            self.config["environment"]["max_trade_amount"],
                        )
                        best_trade = (
                            other_agent_id,
                            give_item,
                            want_item,
                            desired_amount,
                        )

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
        primary_reward = self.inventory[self.desired_item]

        # Bonus for improvement over generation start
        improvement_bonus = (
            self.inventory[self.desired_item]
            - self.generation_start_inventory[self.desired_item]
        )

        # Penalty for having zero of desired item
        zero_penalty = -10.0 if self.inventory[self.desired_item] == 0 else 0.0

        # Small bonus for successful trades (encourages activity)
        trade_bonus = self.successful_trades * 0.1

        # NEW: Strategic value based on trading opportunities
        strategic_value = (
            self._calculate_strategic_value(market_data) if market_data else 0.0
        )

        # Diversity bonus: small reward for having diverse inventory
        # diversity_bonus = self._calculate_diversity_bonus()
        diversity_bonus = 0.0

        total_reward = (
            primary_reward
            + improvement_bonus
            + zero_penalty
            + trade_bonus
            + strategic_value
            + diversity_bonus
        )
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
            item_strategic_value = (
                item_quantity * best_conversion_rate * discount_factor
            )
            strategic_value += item_strategic_value

        return strategic_value

    def _calculate_diversity_bonus(self):
        """
        Calculate a small bonus for maintaining diverse inventory.

        This encourages agents to keep some of all items rather than
        specializing too heavily, which helps maintain trading opportunities.

        Returns:
            Small diversity bonus (typically 0-2 points)
        """
        # Count how many different items we have (non-zero quantities)
        items_held = sum(1 for amount in self.inventory.values() if amount > 0)

        # Bonus scales with number of different items held
        max_diversity = len(self.items_list)
        diversity_ratio = items_held / max_diversity

        # Small bonus (max 1.0 points) for diversity
        diversity_bonus = diversity_ratio * 1.0

        return diversity_bonus

    def _calculate_strategic_value_for_item(self, item_name, market_data=None):
        """
        Calculate strategic value for acquiring a specific item.

        This evaluates how valuable it would be to acquire this item based on
        potential trading paths to our desired item.

        Args:
            item_name: Name of the item to evaluate
            market_data: Dictionary of other agents' trading matrices

        Returns:
            Strategic value score (0.0 if no value, higher = more valuable)
        """
        if not market_data or len(market_data) <= 1:
            return 0.0

        # If this IS our desired item, it has maximum direct value
        if item_name == self.desired_item:
            return 1.0

        # Find item indices
        try:
            item_idx = self.items_list.index(item_name)
            desired_item_idx = self.items_list.index(self.desired_item)
        except ValueError:
            return 0.0  # Item not in our items list

        # Calculate best conversion rate from this item to our desired item
        best_conversion_rate = self._find_best_conversion_path(
            item_idx, desired_item_idx, market_data, max_hops=3
        )

        if best_conversion_rate <= 0:
            return 0.0

        # Strategic value factors:
        # 1. Conversion rate (how much desired item we can get)
        # 2. Market availability (how many agents want this item)
        # 3. Distance penalty for indirect paths

        # Market availability: count how many agents are willing to trade for this item
        market_demand = 0
        total_agents = 0

        for agent_id, other_matrix in market_data.items():
            if agent_id == self.agent_id:
                continue
            total_agents += 1

            # Check if this agent wants the item (any positive rate in their matrix)
            for give_item_idx in range(len(self.items_list)):
                if other_matrix[give_item_idx, item_idx] > 0:
                    market_demand += 1
                    break  # This agent wants the item

        # Market availability factor (0.1 to 1.0)
        market_factor = (
            (market_demand / max(total_agents, 1)) if total_agents > 0 else 0.1
        )
        market_factor = max(0.1, min(1.0, market_factor))

        # Base strategic value
        strategic_value = best_conversion_rate * market_factor

        # Apply discount for indirect trading (prefer direct paths)
        # Estimate path length based on conversion rate quality
        if best_conversion_rate >= 0.8:
            path_discount = 1.0  # Likely direct or very good path
        elif best_conversion_rate >= 0.4:
            path_discount = 0.7  # Likely 2-hop path
        else:
            path_discount = 0.4  # Likely 3+ hop path

        strategic_value *= path_discount

        # Threshold: only consider items with meaningful strategic value
        min_threshold = 0.05
        return strategic_value if strategic_value >= min_threshold else 0.0

    def _get_recent_trade_partners(self, lookback_window=3):
        """
        Get agents we've recently traded with to avoid immediate cycles.

        Args:
            lookback_window: Number of recent trades to consider

        Returns:
            Dict mapping agent_id to list of recent trade info
        """
        recent_partners = defaultdict(list)

        # Look at last N trades
        recent_trades = (
            self.trade_history[-lookback_window:] if self.trade_history else []
        )

        for trade in recent_trades:
            partner_id = trade["partner"]
            trade_info = {
                "gave": trade["given"][0],  # Item we gave
                "received": trade["received"][0],  # Item we received
                "timestep": trade["timestep"],
            }
            recent_partners[partner_id].append(trade_info)

        return recent_partners

    def _would_create_cycle(
        self, target_agent_id, item_giving, item_wanting, recent_partners
    ):
        """
        Check if this trade would create an immediate cycle.

        Args:
            target_agent_id: ID of agent we want to trade with
            item_giving: Item we're offering
            item_wanting: Item we want
            recent_partners: Recent trade partner information

        Returns:
            True if this would create a cycle, False otherwise
        """
        if target_agent_id not in recent_partners:
            return False

        # Check if we recently traded the reverse of this trade with the same agent
        for trade_info in recent_partners[target_agent_id]:
            # Cycle detected if:
            # - We previously gave them item_wanting
            # - We previously received item_giving from them
            # This would mean: A gives X for Y to B, then A gives Y for X to B
            if (
                trade_info["gave"] == item_wanting
                and trade_info["received"] == item_giving
            ):
                return True

        return False

    def _calculate_cycle_penalty(self, target_agent_id, recent_partners):
        """
        Calculate penalty for trading with recently traded partners.

        Args:
            target_agent_id: ID of potential trading partner
            recent_partners: Recent trade partner information

        Returns:
            Penalty factor (0.0 to 1.0, where 1.0 = no penalty)
        """
        if target_agent_id not in recent_partners:
            return 1.0  # No penalty for new partners

        # Calculate penalty based on how recent and frequent trades were
        trade_count = len(recent_partners[target_agent_id])

        # More recent and frequent trades = higher penalty
        if trade_count >= 3:
            return 0.1  # Heavy penalty for frequent recent trading
        elif trade_count >= 2:
            return 0.3  # Moderate penalty
        else:
            return 0.7  # Light penalty

    def _find_best_conversion_path(
        self, from_item_idx, to_item_idx, market_data, max_hops=3
    ):
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

        # Simple policy gradient update - but only occasionally to slow learning
        if (
            len(self.reward_history) >= 2 and len(self.reward_history) % 5 == 0
        ):  # Update every 5 timesteps
            # Calculate advantage (reward improvement)
            advantage = reward - self.reward_history[-2]

            # Update network if we have enough experience
            if len(self.trade_history) > 0:
                # Use last state and action for update
                last_state = self.get_state_vector()

                # Create target (current trading matrix + advantage signal)
                target = torch.FloatTensor(self.trading_matrix.flatten())
                if advantage > 0:
                    target *= 1.005  # Much smaller increase (was 1.01)
                else:
                    target *= 0.995  # Much smaller decrease (was 0.99)

                # Forward pass
                predicted = self.network(last_state.unsqueeze(0))

                # Calculate loss
                loss = F.mse_loss(predicted, target.unsqueeze(0))

                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

    def execute_trade(
        self, trade_partner_id, item_given, amount_given, item_received, amount_received
    ):
        """Execute a trade transaction."""
        # Update inventory
        self.inventory[item_given] -= amount_given
        self.inventory[item_received] += amount_received

        # Ensure non-negative inventory
        self.inventory[item_given] = max(0, self.inventory[item_given])

        # Record trade
        trade_record = {
            "partner": trade_partner_id,
            "given": (item_given, amount_given),
            "received": (item_received, amount_received),
            "timestep": len(self.trade_history),
        }
        self.trade_history.append(trade_record)
        self.successful_trades += 1

        logger.debug(
            f"Agent {self.agent_id} traded {amount_given} {item_given} for {amount_received} {item_received}"
        )

    def reset_for_new_generation(self):
        """Reset agent state for a new generation."""
        # Reset to fresh random inventory to prevent depletion
        self.inventory = {item: np.random.randint(5, 20) for item in self.items_list}
        self.generation_start_inventory = self.inventory.copy()
        self.successful_trades = 0
        self.attempted_trades = 0
        self.trade_history = []
        # Keep reward history for learning

        # Reset position to encourage spatial diversity
        self.position = np.random.uniform(
            0, self.config["environment"]["world_size"], 2
        )

    def get_fitness(self, market_data=None):
        """Calculate fitness score for genetic algorithm selection."""
        return self.calculate_reward(market_data)

    def mutate(self, mutation_rate=0.1):
        """Apply mutation to the agent's parameters."""
        if np.random.random() < mutation_rate:
            # Mutate neural network weights with stronger noise
            with torch.no_grad():
                for param in self.network.parameters():
                    noise = (
                        torch.randn_like(param) * 0.05
                    )  # Increased from 0.01 to 0.05
                    param.add_(noise)

        # Mutate trading matrix directly to add diversity
        if np.random.random() < mutation_rate:
            matrix_noise = np.random.normal(
                0, 0.3, self.trading_matrix.shape
            )  # Increased from 0.1 to 0.3
            self.trading_matrix += matrix_noise
            # Keep values positive and within bounds
            self.trading_matrix = np.maximum(self.trading_matrix, 0.1)
            self.trading_matrix = np.minimum(self.trading_matrix, 10.0)
            # Ensure diagonal stays 1
            np.fill_diagonal(self.trading_matrix, 1.0)

        # Mutate position slightly
        position_noise = np.random.normal(0, 1.0, 2)
        self.position += position_noise

        # Keep position within bounds
        world_size = self.config["environment"]["world_size"]
        self.position = np.clip(self.position, 0, world_size)

    def save_model(self, filepath):
        """Save agent's neural network state."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            checkpoint = {
                "network_state_dict": self.network.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "agent_id": self.agent_id,
                "desired_item": self.desired_item,
                "inventory": self.inventory,
                "trading_matrix": self.trading_matrix,
                "position": self.position,
                "reward_history": self.reward_history,
            }
            torch.save(checkpoint, filepath)
            logger.info(f"Agent {self.agent_id} model saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save agent {self.agent_id} model: {e}")

    def load_model(self, filepath):
        """Load agent's neural network state."""
        if os.path.exists(filepath):
            try:
                checkpoint = torch.load(
                    filepath, map_location="cpu", weights_only=False
                )
                self.network.load_state_dict(checkpoint["network_state_dict"])
                self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
                self.inventory = checkpoint.get("inventory", self.inventory)
                self.trading_matrix = checkpoint.get(
                    "trading_matrix", self.trading_matrix
                )
                self.position = checkpoint.get("position", self.position)
                self.reward_history = checkpoint.get("reward_history", [])
                logger.info(f"Agent {self.agent_id} model loaded from {filepath}")
                return True
            except Exception as e:
                logger.error(f"Failed to load agent {self.agent_id} model: {e}")
                return False
        return False
