import logging
import os
import sys
import numpy as np
from typing import Dict, List, Any


class SafeFormatter(logging.Formatter):
    """Custom formatter that safely handles Unicode characters for Windows console"""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # If encoding fails, replace problematic characters
            formatted = super().format(record)
            # Replace common emoji characters with text equivalents
            replacements = {
                '🎬': '[DEMO]',
                '🚀': '[SUCCESS]',
                '✅': '[OK]',
                '⚠️': '[WARNING]',
                '❌': '[ERROR]',
                '📦': '[LOADING]',
                '🏃': '[RUNNING]',
                '📊': '[STATS]',
                '💡': '[TIP]',
                '🧪': '[TEST]',
                '🎉': '[COMPLETE]',
                '🏆': '[WINNER]',
                '⏹️': '[STOPPED]'
            }
            for emoji, replacement in replacements.items():
                formatted = formatted.replace(emoji, replacement)
            return formatted


def setup_logging(config, append_mode=False):
    """Set up logging to both console and file with proper UTF-8 encoding."""
    # Try to set console to UTF-8 mode on Windows
    try:
        if sys.platform.startswith('win'):
            # Enable UTF-8 mode for Windows console
            os.system('chcp 65001 > nul 2>&1')
    except:
        pass  # Ignore if this fails
    
    log_file = config['logging']['log_file']
    log_level = getattr(logging, config['logging']['level'])
    log_format = config['logging']['format']
    
    # Create directory for log file if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Clear any existing handlers on the root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    
    # Choose file mode based on whether we're resuming training
    file_mode = 'a' if append_mode else 'w'
    mode_description = "append mode (resuming)" if append_mode else "overwrite mode (fresh start)"
    
    # Create formatters
    safe_formatter = SafeFormatter(log_format)  # For console (safe encoding)
    utf8_formatter = logging.Formatter(log_format)  # For file (UTF-8)
    
    # Create console handler with UTF-8 encoding support
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(safe_formatter)  # Use safe formatter for console
    
    # Create file handler with explicit UTF-8 encoding
    file_handler = logging.FileHandler(log_file, mode=file_mode, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(utf8_formatter)  # Use UTF-8 formatter for file
    
    # Configure root logger
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return log_file, mode_description


def calculate_trade_statistics(trade_history: List[Dict]) -> Dict[str, Any]:
    """
    Calculate statistics from trade history.
    
    Args:
        trade_history: List of trade records
        
    Returns:
        Dictionary with trade statistics
    """
    if not trade_history:
        return {
            'total_trades': 0,
            'unique_traders': 0,
            'avg_trades_per_timestep': 0,
            'most_traded_items': {},
            'trade_network_density': 0
        }
    
    # Basic counts
    total_trades = len(trade_history)
    
    # Unique traders
    traders = set()
    for trade in trade_history:
        traders.add(trade['requester_id'])
        traders.add(trade['target_id'])
    unique_traders = len(traders)
    
    # Trades per timestep
    timesteps = set(trade['timestep'] for trade in trade_history)
    avg_trades_per_timestep = total_trades / len(timesteps) if timesteps else 0
    
    # Most traded items
    item_counts = {}
    for trade in trade_history:
        item_given = trade['requester_gave'][0]
        item_received = trade['requester_received'][0]
        
        item_counts[item_given] = item_counts.get(item_given, 0) + 1
        item_counts[item_received] = item_counts.get(item_received, 0) + 1
    
    # Sort items by trade frequency
    most_traded_items = dict(sorted(item_counts.items(), key=lambda x: x[1], reverse=True))
    
    # Trade network density (what fraction of possible agent pairs have traded)
    trading_pairs = set()
    for trade in trade_history:
        pair = tuple(sorted([trade['requester_id'], trade['target_id']]))
        trading_pairs.add(pair)
    
    max_possible_pairs = unique_traders * (unique_traders - 1) / 2 if unique_traders > 1 else 1
    trade_network_density = len(trading_pairs) / max_possible_pairs
    
    return {
        'total_trades': total_trades,
        'unique_traders': unique_traders,
        'avg_trades_per_timestep': avg_trades_per_timestep,
        'most_traded_items': most_traded_items,
        'trade_network_density': trade_network_density,
        'unique_trading_pairs': len(trading_pairs)
    }


def calculate_fitness_statistics(agents: List) -> Dict[str, float]:
    """
    Calculate fitness statistics for a population of agents.
    
    Args:
        agents: List of agent objects
        
    Returns:
        Dictionary with fitness statistics
    """
    if not agents:
        return {
            'best_fitness': 0,
            'worst_fitness': 0,
            'avg_fitness': 0,
            'median_fitness': 0,
            'fitness_std': 0
        }
    
    fitnesses = [agent.get_fitness() for agent in agents]  # Note: market_data not passed in utils context
    
    return {
        'best_fitness': max(fitnesses),
        'worst_fitness': min(fitnesses),
        'avg_fitness': np.mean(fitnesses),
        'median_fitness': np.median(fitnesses),
        'fitness_std': np.std(fitnesses)
    }


def analyze_trading_matrices(agents: List, items_list: List[str]) -> Dict[str, Any]:
    """
    Analyze trading matrices across all agents.
    
    Args:
        agents: List of agent objects
        items_list: List of item names
        
    Returns:
        Dictionary with trading matrix analysis
    """
    if not agents:
        return {}
    
    # Collect all trading matrices
    matrices = [agent.trading_matrix for agent in agents]
    
    # Calculate average trading matrix
    avg_matrix = np.mean(matrices, axis=0)
    
    # Calculate standard deviation matrix
    std_matrix = np.std(matrices, axis=0)
    
    # Find most and least volatile trading pairs
    volatility_flat = std_matrix.flatten()
    most_volatile_idx = np.argmax(volatility_flat)
    least_volatile_idx = np.argmin(volatility_flat)
    
    num_items = len(items_list)
    most_volatile_pair = (
        items_list[most_volatile_idx // num_items],
        items_list[most_volatile_idx % num_items]
    )
    least_volatile_pair = (
        items_list[least_volatile_idx // num_items],
        items_list[least_volatile_idx % num_items]
    )
    
    return {
        'avg_trading_matrix': avg_matrix.tolist(),
        'std_trading_matrix': std_matrix.tolist(),
        'most_volatile_pair': most_volatile_pair,
        'least_volatile_pair': least_volatile_pair,
        'avg_volatility': np.mean(std_matrix),
        'max_volatility': np.max(std_matrix),
        'min_volatility': np.min(std_matrix)
    }


def calculate_inventory_diversity(agents: List, items_list: List[str]) -> Dict[str, float]:
    """
    Calculate inventory diversity statistics.
    
    Args:
        agents: List of agent objects
        items_list: List of item names
        
    Returns:
        Dictionary with inventory diversity statistics
    """
    if not agents:
        return {}
    
    # Calculate Shannon diversity index for each agent's inventory
    diversities = []
    
    for agent in agents:
        inventory_values = [agent.inventory[item] for item in items_list]
        total_items = sum(inventory_values)
        
        if total_items == 0:
            diversities.append(0)
            continue
        
        # Calculate Shannon diversity
        shannon_diversity = 0
        for count in inventory_values:
            if count > 0:
                proportion = count / total_items
                shannon_diversity -= proportion * np.log(proportion)
        
        diversities.append(shannon_diversity)
    
    return {
        'avg_inventory_diversity': np.mean(diversities),
        'max_inventory_diversity': np.max(diversities),
        'min_inventory_diversity': np.min(diversities),
        'diversity_std': np.std(diversities)
    }


def format_agent_summary(agent) -> str:
    """
    Format a summary string for an agent.
    
    Args:
        agent: Agent object
        
    Returns:
        Formatted summary string
    """
    inventory_str = ", ".join([f"{item}:{amount}" for item, amount in agent.inventory.items()])
    
    return (f"Agent {agent.agent_id}: "
            f"Wants {agent.desired_item}, "
            f"Fitness: {agent.get_fitness():.2f}, "  # Note: market_data not available in utils context
            f"Trades: {agent.successful_trades}, "
            f"Inventory: [{inventory_str}]")


def save_analysis_report(env, output_path: str):
    """
    Save a comprehensive analysis report of the current environment state.
    
    Args:
        env: TradingEnvironment instance
        output_path: Path to save the report
    """
    try:
        # Calculate various statistics
        trade_stats = calculate_trade_statistics(env.trade_history)
        fitness_stats = calculate_fitness_statistics(env.agents)
        matrix_analysis = analyze_trading_matrices(env.agents, env.items_list)
        inventory_diversity = calculate_inventory_diversity(env.agents, env.items_list)
        
        # Create report content
        report_lines = [
            "=" * 80,
            f"TRADING ENVIRONMENT ANALYSIS REPORT",
            f"Generated at timestep {env.current_timestep}, generation {env.current_generation}",
            "=" * 80,
            "",
            "POPULATION OVERVIEW:",
            f"  Total agents: {len(env.agents)}",
            f"  Items available: {', '.join(env.items_list)}",
            f"  World size: {env.world_size}",
            "",
            "FITNESS STATISTICS:",
            f"  Best fitness: {fitness_stats['best_fitness']:.2f}",
            f"  Average fitness: {fitness_stats['avg_fitness']:.2f}",
            f"  Worst fitness: {fitness_stats['worst_fitness']:.2f}",
            f"  Fitness std dev: {fitness_stats['fitness_std']:.2f}",
            "",
            "TRADING STATISTICS:",
            f"  Total trades: {trade_stats['total_trades']}",
            f"  Unique traders: {trade_stats['unique_traders']}",
            f"  Avg trades per timestep: {trade_stats['avg_trades_per_timestep']:.2f}",
            f"  Trade network density: {trade_stats['trade_network_density']:.3f}",
            "",
            "MOST TRADED ITEMS:",
        ]
        
        for item, count in list(trade_stats['most_traded_items'].items())[:5]:
            report_lines.append(f"  {item}: {count} trades")
        
        report_lines.extend([
            "",
            "INVENTORY DIVERSITY:",
            f"  Average diversity: {inventory_diversity.get('avg_inventory_diversity', 0):.3f}",
            f"  Max diversity: {inventory_diversity.get('max_inventory_diversity', 0):.3f}",
            f"  Min diversity: {inventory_diversity.get('min_inventory_diversity', 0):.3f}",
            "",
            "TRADING MATRIX ANALYSIS:",
            f"  Average volatility: {matrix_analysis.get('avg_volatility', 0):.3f}",
            f"  Most volatile pair: {matrix_analysis.get('most_volatile_pair', 'N/A')}",
            f"  Least volatile pair: {matrix_analysis.get('least_volatile_pair', 'N/A')}",
            "",
            "TOP 5 AGENTS BY FITNESS:",
        ])
        
        # Sort agents by fitness and add top 5
        sorted_agents = sorted(env.agents, key=lambda a: a.get_fitness(env.market_data), reverse=True)
        for i, agent in enumerate(sorted_agents[:5]):
            report_lines.append(f"  {i+1}. {format_agent_summary(agent)}")
        
        report_lines.extend([
            "",
            "GENERATION HISTORY:",
        ])
        
        # Add recent generation stats
        for gen_stat in env.generation_stats[-5:]:
            report_lines.append(
                f"  Gen {gen_stat['generation']}: "
                f"Best={gen_stat['best_fitness']:.2f}, "
                f"Avg={gen_stat['avg_fitness']:.2f}, "
                f"Trades={gen_stat['total_trades']}"
            )
        
        report_lines.append("=" * 80)
        
        # Write report to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logging.getLogger(__name__).info(f"Analysis report saved to {output_path}")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save analysis report: {e}")


def validate_config(config: Dict) -> bool:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_sections = ['environment', 'network', 'learning', 'training', 'server', 'logging']
    
    for section in required_sections:
        if section not in config:
            logging.getLogger(__name__).error(f"Missing required config section: {section}")
            return False
    
    # Validate environment config
    env_config = config['environment']
    required_env_keys = ['world_size', 'max_trade_distance', 'items_list', 'population_size']
    
    for key in required_env_keys:
        if key not in env_config:
            logging.getLogger(__name__).error(f"Missing required environment config: {key}")
            return False
    
    # Validate items list
    if not isinstance(env_config['items_list'], list) or len(env_config['items_list']) < 2:
        logging.getLogger(__name__).error("items_list must be a list with at least 2 items")
        return False
    
    # Validate population size
    if env_config['population_size'] < 2:
        logging.getLogger(__name__).error("population_size must be at least 2")
        return False
    
    return True
