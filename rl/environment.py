import numpy as np
from dotenv import load_dotenv
import re
import os
import random
import logging
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from imagine import ChatMessage, ImagineClient

logger = logging.getLogger(__name__)

load_dotenv()

class TradingEnvironment:
    def __init__(self, config):
        """
        Initialize the multi-agent trading environment.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        env_config = config['environment']
        
        # Environment parameters
        self.world_size = env_config['world_size']
        self.max_trade_distance = env_config['max_trade_distance']
        self.max_trade_amount = env_config['max_trade_amount']
        self.items_list = env_config['items_list']
        self.num_items = len(self.items_list)
        
        # Genetic algorithm parameters
        self.population_size = env_config['population_size']
        self.generation_length = env_config['generation_length']  # timesteps per generation
        self.survival_rate = env_config['survival_rate']  # fraction that survives
        self.mutation_rate = env_config['mutation_rate']
        
        # Current state
        self.agents = []
        self.current_timestep = 0
        self.current_generation = 0
        self.market_data = {}  # agent_id -> trading_matrix
        self.agent_positions = {}  # agent_id -> (x, y)
        
        # Statistics tracking
        self.generation_stats = []
        self.trade_history = []
        
    def initialize_agents(self, agent_class):
        """
        Initialize the population of trading agents.
        
        Args:
            agent_class: Class to use for creating agents
        """
        self.agents = []

        self.client = ImagineClient(api_key= os.getenv('IMAGINE_API'), endpoint= os.getenv('IMAGINE_ENDPOINT_URL'))
        
        for i in range(self.population_size):
            # Random desired item for each agent
            desired_item = random.choice(self.items_list)
            
            # Create agent
            agent = agent_class(
                agent_id=f"agent_{i}",
                config=self.config,
                items_list=self.items_list,
                desired_item=desired_item
            )
            
            self.agents.append(agent)
            self.agent_positions[agent.agent_id] = agent.position
        
        logger.info(f"Initialized {len(self.agents)} agents")
        
    def step(self) -> Dict:
        """
        Execute one timestep of the environment.
        
        Returns:
            Dictionary with step information
        """
        step_info = {
            'timestep': self.current_timestep,
            'generation': self.current_generation,
            'trades_executed': 0,
            'total_reward': 0
        }
        
        # Phase 1: Agents update their trading matrices
        self._update_trading_matrices()
        
        # Phase 2: Collect all trading matrices for public access
        self._collect_market_data()
        
        # Phase 3: Agents select trade actions
        trade_requests = self._collect_trade_requests()
        
        # Phase 4: Resolve conflicting trades and execute
        executed_trades = self._resolve_and_execute_trades(trade_requests)
        step_info['trades_executed'] = len(executed_trades)
        
        # Phase 5: Update agent policies and calculate rewards
        total_reward = self._update_agents_and_calculate_rewards()
        step_info['total_reward'] = total_reward
        
        self.current_timestep += 1
        
        # Check if generation is complete
        if self.current_timestep % self.generation_length == 0:
            self._end_generation()
            step_info['generation_ended'] = True
        
        return step_info
    
    def _update_trading_matrices(self):
        """Phase 1: Each agent updates its trading matrix."""
        for agent in self.agents:
            agent.update_trading_matrix(self.market_data)
    
    def _collect_market_data(self):
        """Phase 2: Collect all trading matrices for public access."""
        self.market_data = {}
        self.agent_positions = {}
        
        

        for agent in self.agents:
            self.market_data[agent.agent_id] = agent.trading_matrix.copy()
            self.agent_positions[agent.agent_id] = agent.position.copy()
    
    def _collect_trade_requests(self) -> List[Tuple]:
        """
        Phase 3: Collect trade requests from all agents.
        
        Returns:
            List of valid trade requests: (b_i, b_j, D_i, D_j, D_j_amt)
            where b_i = requester_id, b_j = target_id, D_i = item_giving, 
            D_j = item_wanting, D_j_amt = amount_wanting
        """
        trade_requests = []
        
        for agent in self.agents:
            agent.attempted_trades += 1
            trade_action = agent.select_trade_action(self.market_data, self.agent_positions)
            
            if trade_action is not None:
                target_agent_id, item_giving, item_wanting, amount_wanting = trade_action

                chat_reponse = self.client.chat(
                    messages=[
                        ChatMessage(role="system", content="You are a trading agent, you receive a dictionary (market_data) where " \
                        "the keys are the ids of " \
                        "all trading agents (including yourself) and the values are their corresponding trading matrix. " \
                        "A trading matrix is an n by n matrix where n is the size of the number of items available, " \
                        "each element A_ij in the matrix represents how many of the items[j] the agent is willing to " \
                        "trade 1 of its items[i] for, where items is the list of all available items. You also receive a " \
                        "preliminary trade request in the form of (b_i, b_j, D_i, D_j, D_amt), where b_i is your id, b_j is " \
                        "the id of the agent you want to trade, D_i is the item you are offering, D_j is the item you expect to " \
                        "receive from agent b_j, and D_amt is the amount of D_j you want. You also receive your current inventory, and the item" \
                        "whose quantity you want to maximize (want_item). Your job is to determine if this prelimiary trade request is any good" \
                        "if it is return it, if it is not, then return a new trade request in the format (b_i, b_j, D_i, D_j, D_amt)." \
                        "Ensure that your response only consists of the trade request you want (either the preliminary one or something " \
                        "you come up with) and nothing else"),

                        ChatMessage(role="system", content="input:" \
                                                f"market_data: {self.market_data}" \
                                                f"inventory: {agent.inventory}" \
                                                f"want_item: {agent.desired_item}"),
                        ChatMessage(role="user", content="Given the following preliminary trade request:" \
                                                f"({agent.agent_id, target_agent_id, item_giving, item_wanting, amount_wanting})" \
                                                "Return the most optimal trade request given all the information you have" \
                                                "(either return this preliminary trade request or come up with another" \
                                                "with the correct format)")
                    ],
                    model="DeepSeek-R1-Distill-Llama-70B",
                )

                match = re.search(r"\(([^)]+)\)", chat_reponse.first_content)

                pass_through = False

                tokens = []

                if match:
                    tokens = [x.strip() for x in match.group(1).split(',')]
                    if agent.agent_id != tokens[0]:
                        pass_through = True
                    if len(tokens) != 5:
                        pass_through = True
                    if tokens[2] not in self.items_list or tokens[3] not in self.items_list:
                        pass_through = True 
                    try:
                        int(tokens[0][-1])
                        int(tokens[1][-1])
                        float(tokens[4])
                    except:
                        pass_through = True
                else:
                    pass_through = True
                
                if not pass_through:
                    target_agent_id = tokens[1]
                    item_giving = tokens[2]
                    item_wanting = tokens[3]
                    amount_wanting = tokens[4]

                # Validate trade request
                if self._validate_trade_request(agent, target_agent_id, item_giving, item_wanting, amount_wanting):
                    trade_requests.append((agent.agent_id, target_agent_id, item_giving, item_wanting, amount_wanting))
                else:
                    logger.debug(f"Invalid trade request from {agent.agent_id}: insufficient resources")
        
        return trade_requests
    
    def _validate_trade_request(self, requester_agent, target_agent_id, item_giving, item_wanting, amount_wanting):
        """
        Validate that a trade request is feasible.
        
        Args:
            requester_agent: The agent making the request
            target_agent_id: ID of target agent
            item_giving: Item the requester is offering
            item_wanting: Item the requester wants
            amount_wanting: Amount of item_wanting desired
            
        Returns:
            True if trade request is valid, False otherwise
        """
        # Check if requester has the item they're offering
        if requester_agent.inventory[item_giving] <= 0:
            return False
        
        # Find target agent
        target_agent = None
        for agent in self.agents:
            if agent.agent_id == target_agent_id:
                target_agent = agent
                break
        
        if target_agent is None:
            return False
        
        # Check if target has enough of the wanted item
        if target_agent.inventory[item_wanting] < amount_wanting:
            return False
        
        # Check if target is willing to make this trade based on their trading matrix
        item_giving_idx = self.items_list.index(item_giving)
        item_wanting_idx = self.items_list.index(item_wanting)
        
        # Target's rate: how much of item_giving they want for 1 unit of item_wanting
        target_rate = target_agent.trading_matrix[item_wanting_idx, item_giving_idx]
        
        if target_rate <= 0:
            return False
        
        # Calculate how much the requester needs to give
        required_giving_amount = amount_wanting / target_rate
        
        # Check if requester has enough to give
        if requester_agent.inventory[item_giving] < required_giving_amount:
            return False
        
        return True
    
    def _resolve_and_execute_trades(self, trade_requests: List[Tuple]) -> List[Dict]:
        """
        Phase 4: Resolve conflicting trades and execute valid ones.
        
        Args:
            trade_requests: List of trade requests
            
        Returns:
            List of executed trades
        """
        executed_trades = []
        
        # Group requests by target agent
        requests_by_target = defaultdict(list)
        for request in trade_requests:
            requester_id, target_id, item_giving, item_wanting, amount_wanting = request
            requests_by_target[target_id].append(request)
        
        # Process each target agent's incoming requests
        for target_id, requests in requests_by_target.items():
            if len(requests) == 1:
                # No conflict, try to execute trade
                trade = self._try_execute_trade(requests[0])
                if trade:
                    executed_trades.append(trade)
            else:
                # Multiple agents want to trade with same target
                # Select based on distance (closer has higher probability)
                selected_request = self._select_trade_by_distance(target_id, requests)
                if selected_request:
                    trade = self._try_execute_trade(selected_request)
                    if trade:
                        executed_trades.append(trade)
        
        return executed_trades
    
    def _select_trade_by_distance(self, target_id: str, requests: List[Tuple]) -> Optional[Tuple]:
        """
        Select trade request based on distance probability.
        
        Args:
            target_id: ID of the target agent
            requests: List of competing trade requests
            
        Returns:
            Selected request or None
        """
        if target_id not in self.agent_positions:
            return None
        
        target_pos = self.agent_positions[target_id]
        
        # Calculate distances and probabilities
        distances = []
        for request in requests:
            requester_id = request[0]
            if requester_id in self.agent_positions:
                requester_pos = self.agent_positions[requester_id]
                distance = np.linalg.norm(np.array(target_pos) - np.array(requester_pos))
                distances.append(distance)
            else:
                distances.append(float('inf'))
        
        # Convert distances to probabilities (inverse relationship)
        probabilities = []
        for distance in distances:
            if distance == float('inf'):
                probabilities.append(0.0)
            else:
                probabilities.append(1.0 / (1.0 + distance))
        
        # Normalize probabilities
        total_prob = sum(probabilities)
        if total_prob == 0:
            return None
        
        probabilities = [p / total_prob for p in probabilities]
        
        # Select based on probability
        selected_idx = np.random.choice(len(requests), p=probabilities)
        return requests[selected_idx]
    
    def _try_execute_trade(self, request: Tuple) -> Optional[Dict]:
        """
        Try to execute a trade request.
        
        Args:
            request: Trade request tuple (b_i, b_j, D_i, D_j, D_j_amt)
            
        Returns:
            Trade information dict or None if trade failed
        """
        requester_id, target_id, item_giving, item_wanting, amount_wanting = request
        
        # Find agent objects
        requester = None
        target = None
        
        for agent in self.agents:
            if agent.agent_id == requester_id:
                requester = agent
            elif agent.agent_id == target_id:
                target = agent
        
        if not requester or not target:
            return None
        
        # Validate trade is still possible (double-check)
        if not self._validate_trade_request(requester, target_id, item_giving, item_wanting, amount_wanting):
            return None
        
        # Calculate how much the requester needs to give based on target's trading matrix
        item_giving_idx = self.items_list.index(item_giving)
        item_wanting_idx = self.items_list.index(item_wanting)
        
        # Target's rate: how much of item_giving they want for 1 unit of item_wanting
        target_rate = target.trading_matrix[item_wanting_idx, item_giving_idx]
        
        if target_rate <= 0:
            return None
        
        # Calculate actual trade amounts
        required_giving_amount = amount_wanting / target_rate
        
        # Ensure we don't exceed available inventory
        actual_giving_amount = min(required_giving_amount, requester.inventory[item_giving])
        actual_wanting_amount = min(amount_wanting, target.inventory[item_wanting])
        
        # Recalculate based on what's actually available
        if actual_giving_amount * target_rate > actual_wanting_amount:
            actual_giving_amount = actual_wanting_amount / target_rate
        else:
            actual_wanting_amount = actual_giving_amount * target_rate
        
        if actual_giving_amount <= 0 or actual_wanting_amount <= 0:
            return None
        
        # Execute the trade
        requester.inventory[item_giving] -= actual_giving_amount
        requester.inventory[item_wanting] += actual_wanting_amount
        
        target.inventory[item_wanting] -= actual_wanting_amount
        target.inventory[item_giving] += actual_giving_amount
        
        # Ensure non-negative inventories
        requester.inventory[item_giving] = max(0, requester.inventory[item_giving])
        target.inventory[item_wanting] = max(0, target.inventory[item_wanting])
        
        # Record trade for both agents
        trade_info = {
            'requester_id': requester_id,
            'target_id': target_id,
            'requester_gave': (item_giving, actual_giving_amount),
            'requester_received': (item_wanting, actual_wanting_amount),
            'timestep': self.current_timestep
        }
        
        requester.successful_trades += 1
        target.successful_trades += 1
        
        self.trade_history.append(trade_info)
        
        logger.debug(f"Trade executed: {requester_id} gave {actual_giving_amount:.2f} {item_giving} "
                    f"for {actual_wanting_amount:.2f} {item_wanting} from {target_id}")
        
        return trade_info
    
    def _update_agents_and_calculate_rewards(self) -> float:
        """
        Phase 5: Update agent policies and calculate total reward.
        
        Returns:
            Total reward across all agents
        """
        total_reward = 0
        
        for agent in self.agents:
            # Pass market data to reward calculation for strategic value assessment
            reward = agent.calculate_reward(self.market_data)
            agent.update_policy(reward)
            total_reward += reward
        
        return total_reward
    
    def _end_generation(self):
        """End current generation and start genetic algorithm selection."""
        logger.info(f"Ending generation {self.current_generation}")
        
        # Calculate fitness for all agents (using market data for strategic evaluation)
        fitness_scores = [(agent, agent.get_fitness(self.market_data)) for agent in self.agents]
        fitness_scores.sort(key=lambda x: x[1], reverse=True)  # Sort by fitness (descending)
        
        # Record generation statistics
        fitnesses = [score for _, score in fitness_scores]
        gen_stats = {
            'generation': self.current_generation,
            'best_fitness': max(fitnesses),
            'avg_fitness': np.mean(fitnesses),
            'worst_fitness': min(fitnesses),
            'total_trades': len(self.trade_history)
        }
        self.generation_stats.append(gen_stats)
        
        logger.info(f"Generation {self.current_generation} stats: "
                   f"Best={gen_stats['best_fitness']:.2f}, "
                   f"Avg={gen_stats['avg_fitness']:.2f}, "
                   f"Trades={gen_stats['total_trades']}")
        
        # Select survivors (top 50%)
        num_survivors = int(self.population_size * self.survival_rate)
        survivors = [agent for agent, _ in fitness_scores[:num_survivors]]
        
        # Create new generation
        new_agents = []
        
        # Keep survivors
        for agent in survivors:
            agent.reset_for_new_generation()
            new_agents.append(agent)
        
        # Create offspring to fill population
        while len(new_agents) < self.population_size:
            # Select random parent from survivors
            parent = random.choice(survivors)
            
            # Create offspring (copy)
            offspring = self._create_offspring(parent)
            new_agents.append(offspring)
        
        self.agents = new_agents
        self.current_generation += 1
        self.trade_history = []  # Reset trade history for new generation
        
        # Update agent positions
        for agent in self.agents:
            self.agent_positions[agent.agent_id] = agent.position
    
    def _create_offspring(self, parent) -> 'TradingAgent':
        """
        Create offspring from parent agent.
        
        Args:
            parent: Parent agent
            
        Returns:
            New agent (offspring)
        """
        # Import here to avoid circular import
        try:
            from .agent import TradingAgent
        except ImportError:
            from agent import TradingAgent
        
        # Create new agent with same desired item as parent
        offspring = TradingAgent(
            agent_id=f"agent_{len(self.agents)}_{self.current_generation}",
            config=self.config,
            items_list=self.items_list,
            desired_item=parent.desired_item,
            initial_inventory=parent.generation_start_inventory.copy()
        )
        
        # Copy parent's network weights
        offspring.network.load_state_dict(parent.network.state_dict())
        offspring.optimizer.load_state_dict(parent.optimizer.state_dict())
        
        # Copy trading matrix
        offspring.trading_matrix = parent.trading_matrix.copy()
        
        # Apply mutation
        offspring.mutate(self.mutation_rate)
        
        return offspring
    
    def get_state(self) -> Dict:
        """Get current environment state for visualization."""
        agent_states = []
        for agent in self.agents:
            agent_states.append({
                'id': agent.agent_id,
                'position': agent.position.tolist(),
                'inventory': agent.inventory,
                'desired_item': agent.desired_item,
                'fitness': agent.get_fitness(self.market_data),
                'successful_trades': agent.successful_trades
            })
        
        return {
            'timestep': self.current_timestep,
            'generation': self.current_generation,
            'agents': agent_states,
            'recent_trades': self.trade_history[-10:] if self.trade_history else [],
            'generation_stats': self.generation_stats[-5:] if self.generation_stats else []
        }
