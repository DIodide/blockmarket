import time
import logging
import numpy as np
import os
from collections import deque

try:
    from .environment import TradingEnvironment
    from .agent import TradingAgent
except ImportError:
    from environment import TradingEnvironment
    from agent import TradingAgent


logger = logging.getLogger(__name__)


def training_loop(env, simulation_speed, log_frequency, model_save_frequency, 
                 model_save_path, max_generations, target_fitness, 
                 early_stopping_patience, current_state, running_flag):
    """
    Main training loop for multi-agent trading environment.
    
    Args:
        env: TradingEnvironment instance
        simulation_speed: Sleep time between timesteps
        log_frequency: Timesteps between summary logs
        model_save_frequency: Generations between model saves
        model_save_path: Directory to save model checkpoints
        max_generations: Maximum number of generations to run
        target_fitness: Target fitness to consider problem solved
        early_stopping_patience: Stop if no improvement for N generations
        current_state: Shared state dict for web interface
        running_flag: Shared running flag dict
    """
    logger.info("Starting multi-agent trading simulation")
    logger.info(f"Population size: {len(env.agents)}")
    logger.info(f"Items: {env.items_list}")
    logger.info(f"Max generations: {max_generations}")
    logger.info(f"Target fitness: {target_fitness}")
    
    # Initialize tracking variables
    best_fitness_history = deque(maxlen=early_stopping_patience)
    generations_without_improvement = 0
    best_overall_fitness = -float('inf')
    
    # Initialize market data for fitness calculation
    env._collect_market_data()
    
    # Get initial fitness to avoid -inf issue
    try:
        initial_fitness = max([agent.get_fitness(env.market_data) for agent in env.agents])
        if initial_fitness > best_overall_fitness:
            best_overall_fitness = initial_fitness
        logger.info(f"Initial best fitness: {best_overall_fitness:.2f}")
    except Exception as e:
        logger.warning(f"Could not calculate initial fitness: {e}")
        best_overall_fitness = 0.0
    
    try:
        while running_flag['value'] and env.current_generation < max_generations:
            generation_start_time = time.time()
            
            logger.info(f"Starting generation {env.current_generation + 1}")
            
            # Run one generation (multiple timesteps)
            generation_rewards = []
            generation_trades = []
            
            for timestep_in_gen in range(env.generation_length):
                if not running_flag['value']:
                    break
                
                # Execute one timestep (this is where the per-timestep updates happen)
                step_info = env.step()
                
                generation_rewards.append(step_info['total_reward'])
                generation_trades.append(step_info['trades_executed'])
                
                # Update current state for web interface
                env_state = env.get_state()
                current_state.update({
                    'timestep': env.current_timestep,
                    'generation': env.current_generation,
                    'total_agents': len(env.agents),
                    'recent_trades': len(env.trade_history),
                    'avg_fitness': np.mean([agent.get_fitness(env.market_data) for agent in env.agents]),
                    'best_fitness': max([agent.get_fitness(env.market_data) for agent in env.agents]),
                    'generation_progress': (timestep_in_gen + 1) / env.generation_length
                })
                
                # Log progress periodically
                if env.current_timestep % log_frequency == 0:
                    avg_reward = np.mean(generation_rewards[-log_frequency:]) if generation_rewards else 0
                    total_trades = sum(generation_trades[-log_frequency:])
                    logger.info(f"Timestep {env.current_timestep}: "
                              f"Avg reward: {avg_reward:.2f}, "
                              f"Trades: {total_trades}, "
                              f"Generation: {env.current_generation}")
                
                time.sleep(simulation_speed)
            
            if not running_flag['value']:
                break
            
            # Generation completed, get final stats
            generation_time = time.time() - generation_start_time
            current_best_fitness = max([agent.get_fitness(env.market_data) for agent in env.agents])
            avg_fitness = np.mean([agent.get_fitness(env.market_data) for agent in env.agents])
            total_trades_this_gen = sum(generation_trades)
            
            logger.info("="*60)
            logger.info(f"Generation {env.current_generation} completed in {generation_time:.2f}s")
            logger.info(f"Best fitness: {current_best_fitness:.2f}")
            logger.info(f"Average fitness: {avg_fitness:.2f}")
            logger.info(f"Total trades: {total_trades_this_gen}")
            logger.info("="*60)
            
            # Check for improvement
            if current_best_fitness > best_overall_fitness:
                best_overall_fitness = current_best_fitness
                generations_without_improvement = 0
                logger.info(f"🎉 New best fitness achieved: {best_overall_fitness:.2f}")
            else:
                generations_without_improvement += 1
                logger.info(f"No improvement for {generations_without_improvement} generations")
            
            best_fitness_history.append(current_best_fitness)
            
            # Check stopping conditions
            if current_best_fitness >= target_fitness:
                logger.info("="*60)
                logger.info("🏆 TARGET FITNESS ACHIEVED!")
                logger.info(f"Best fitness: {current_best_fitness:.2f}")
                logger.info(f"Target: {target_fitness}")
                logger.info(f"Generation: {env.current_generation}")
                logger.info("="*60)
                break
            
            if generations_without_improvement >= early_stopping_patience:
                logger.info("="*60)
                logger.info("⏹️ EARLY STOPPING - No improvement detected")
                logger.info(f"Best fitness: {best_overall_fitness:.2f}")
                logger.info(f"Generations without improvement: {generations_without_improvement}")
                logger.info("="*60)
                break
            
            # Save models periodically
            if (env.current_generation + 1) % model_save_frequency == 0:
                save_generation_models(env, model_save_path, env.current_generation)
            
            # The genetic algorithm selection happens automatically in env.step()
            # when the generation ends (every generation_length timesteps)
        
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
    except Exception as e:
        logger.error(f"Error in training loop: {e}")
        raise
    finally:
        # Save final models
        logger.info("Saving final models...")
        save_generation_models(env, model_save_path, env.current_generation, final=True)
        
        # Final statistics
        logger.info("="*60)
        logger.info("TRAINING COMPLETED")
        logger.info(f"Total generations: {env.current_generation}")
        logger.info(f"Total timesteps: {env.current_timestep}")
        logger.info(f"Best fitness achieved: {best_overall_fitness:.2f}" if best_overall_fitness != -float('inf') else "Best fitness achieved: No valid fitness recorded")
        logger.info(f"Final average fitness: {np.mean([agent.get_fitness(env.market_data) for agent in env.agents]):.2f}")
        logger.info("="*60)


def save_generation_models(env, model_save_path, generation, final=False):
    """
    Save models for the current generation.
    
    Args:
        env: TradingEnvironment instance
        model_save_path: Base path for saving models
        generation: Current generation number
        final: Whether this is the final save
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(model_save_path, exist_ok=True)
        
        # Sort agents by fitness
        agents_by_fitness = sorted(env.agents, key=lambda a: a.get_fitness(env.market_data), reverse=True)
        
        # Save top 5 agents or all agents if final save
        num_to_save = len(agents_by_fitness) if final else min(5, len(agents_by_fitness))
        
        for i, agent in enumerate(agents_by_fitness[:num_to_save]):
            if final:
                filename = f"agent_{agent.agent_id}_final.pth"
            else:
                filename = f"agent_gen{generation}_rank{i+1}.pth"
            
            filepath = os.path.join(model_save_path, filename)
            agent.save_model(filepath)
        
        # Save environment state
        env_state_path = os.path.join(model_save_path, f"environment_gen{generation}.yaml")
        if final:
            env_state_path = os.path.join(model_save_path, "environment_final.yaml")
        
        import yaml
        env_state = {
            'generation': generation,
            'timestep': env.current_timestep,
            'generation_stats': env.generation_stats,
            'config': env.config
        }
        
        with open(env_state_path, 'w') as f:
            yaml.dump(env_state, f)
        
        logger.info(f"Saved {num_to_save} agent models and environment state")
        
    except Exception as e:
        logger.error(f"Failed to save models: {e}")


def create_training_environment(config):
    """
    Create and initialize the trading environment.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized TradingEnvironment
    """
    env = TradingEnvironment(config)
    env.initialize_agents(TradingAgent)
    
    logger.info(f"Created environment with {len(env.agents)} agents")
    logger.info(f"Items available: {env.items_list}")
    
    # Log agent distribution by desired item
    desired_items_count = {}
    for agent in env.agents:
        item = agent.desired_item
        desired_items_count[item] = desired_items_count.get(item, 0) + 1
    
    logger.info("Agent distribution by desired item:")
    for item, count in desired_items_count.items():
        logger.info(f"  {item}: {count} agents")
    
    return env


def load_saved_environment(config, model_save_path, generation=None):
    """
    Load a previously saved environment and agents.
    
    Args:
        config: Configuration dictionary
        model_save_path: Path where models are saved
        generation: Specific generation to load (None for latest)
        
    Returns:
        Loaded TradingEnvironment or None if loading failed
    """
    try:
        import yaml
        import glob
        
        # Find environment state file
        if generation is not None:
            env_state_path = os.path.join(model_save_path, f"environment_gen{generation}.yaml")
        else:
            # Find latest environment file
            pattern = os.path.join(model_save_path, "environment_gen*.yaml")
            env_files = glob.glob(pattern)
            if not env_files:
                logger.error("No saved environment files found")
                return None
            env_state_path = max(env_files)  # Latest file
        
        if not os.path.exists(env_state_path):
            logger.error(f"Environment state file not found: {env_state_path}")
            return None
        
        # Load environment state
        with open(env_state_path, 'r') as f:
            env_state = yaml.safe_load(f)
        
        # Create environment
        env = TradingEnvironment(config)
        env.current_generation = env_state['generation']
        env.current_timestep = env_state['timestep']
        env.generation_stats = env_state.get('generation_stats', [])
        
        # Load agents (this is more complex and might need manual reconstruction)
        # For now, create new agents - in a full implementation, you'd save/load agent states
        env.initialize_agents(TradingAgent)
        
        logger.info(f"Loaded environment from generation {env.current_generation}")
        return env
        
    except Exception as e:
        logger.error(f"Failed to load saved environment: {e}")
        return None
