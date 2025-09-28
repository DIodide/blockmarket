import torch.nn as nn
import torch.nn.functional as F
import torch


class TradingNetwork(nn.Module):
    def __init__(self, config, num_items):
        super(TradingNetwork, self).__init__()
        self.num_items = num_items
        
        # Calculate input dimension
        # inventory (num_items) + desired_item_one_hot (num_items) + 
        # current_trading_matrix (num_items^2) + market_rates (num_items^2) + 
        # success_rate (1)
        input_dim = num_items + num_items + (num_items * num_items) + (num_items * num_items) + 1
        
        hidden_dim = config['network']['hidden_dim']
        
        # Network layers
        self.shared = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Output layer for trading matrix (flattened)
        self.trading_matrix_head = nn.Linear(hidden_dim, num_items * num_items)
        
    def forward(self, x):
        """
        Forward pass through the network.
        
        Args:
            x: Input state vector
            
        Returns:
            Trading matrix (flattened)
        """
        shared_features = self.shared(x)
        
        # Generate trading matrix
        trading_matrix_flat = self.trading_matrix_head(shared_features)
        
        # Apply softplus to ensure positive values
        trading_matrix_flat = F.softplus(trading_matrix_flat) + 0.1  # Minimum value of 0.1
        
        return trading_matrix_flat


class ValueNetwork(nn.Module):
    """Optional value network for more sophisticated learning."""
    
    def __init__(self, config, num_items):
        super(ValueNetwork, self).__init__()
        self.num_items = num_items
        
        # Same input dimension as TradingNetwork
        input_dim = num_items + num_items + (num_items * num_items) + (num_items * num_items) + 1
        hidden_dim = config['network']['hidden_dim']
        
        self.value_network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
    def forward(self, x):
        """
        Forward pass to estimate state value.
        
        Args:
            x: Input state vector
            
        Returns:
            Estimated state value
        """
        return self.value_network(x)


class ActorCriticNetwork(nn.Module):
    """Combined actor-critic network for more advanced learning."""
    
    def __init__(self, config, num_items):
        super(ActorCriticNetwork, self).__init__()
        self.num_items = num_items
        
        # Input dimension calculation
        input_dim = num_items + num_items + (num_items * num_items) + (num_items * num_items) + 1
        hidden_dim = config['network']['hidden_dim']
        
        # Shared layers
        self.shared = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Actor head (trading matrix)
        self.actor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_items * num_items)
        )
        
        # Critic head (value estimation)
        self.critic = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
    def forward(self, x):
        """
        Forward pass through actor-critic network.
        
        Args:
            x: Input state vector
            
        Returns:
            Tuple of (trading_matrix_flat, state_value)
        """
        shared_features = self.shared(x)
        
        # Actor output (trading matrix)
        trading_matrix_flat = self.actor(shared_features)
        trading_matrix_flat = F.softplus(trading_matrix_flat) + 0.1
        
        # Critic output (state value)
        state_value = self.critic(shared_features)
        
        return trading_matrix_flat, state_value
