#!/usr/bin/env python3
"""
Example demonstrating the strategic value function with indirect trading paths.

This script shows how agents can value items not just for direct trades,
but for their potential in multi-hop trading chains to reach desired items.
"""

import numpy as np
from agent import TradingAgent
from config import load_config


def create_example_scenario():
    """Create a simple example scenario to demonstrate strategic value."""
    config = load_config()
    items_list = ['wood', 'stone', 'iron', 'gold']
    
    # Create three agents with different desired items
    agent_a = TradingAgent('agent_a', config, items_list, 'gold', 
                          initial_inventory={'wood': 10, 'stone': 0, 'iron': 0, 'gold': 0})
    
    agent_b = TradingAgent('agent_b', config, items_list, 'stone',
                          initial_inventory={'wood': 0, 'stone': 5, 'iron': 10, 'gold': 0})
    
    agent_c = TradingAgent('agent_c', config, items_list, 'wood',
                          initial_inventory={'wood': 0, 'stone': 0, 'iron': 0, 'gold': 8})
    
    # Set up trading matrices to create interesting indirect paths
    # Agent A: Wants gold, has wood
    # - Will trade wood for iron at rate 2:1
    # - Will trade wood for stone at rate 1:1
    agent_a.trading_matrix = np.array([
        [1.0, 1.0, 2.0, 0.1],  # wood -> [wood, stone, iron, gold]
        [0.5, 1.0, 1.5, 0.1],  # stone -> [wood, stone, iron, gold]
        [0.3, 0.8, 1.0, 0.1],  # iron -> [wood, stone, iron, gold]
        [10.0, 10.0, 10.0, 1.0]  # gold -> [wood, stone, iron, gold] (very high rates)
    ])
    
    # Agent B: Wants stone, has iron
    # - Will trade iron for gold at rate 1:2 (good rate for gold)
    # - Will trade iron for wood at rate 1:1
    agent_b.trading_matrix = np.array([
        [1.0, 0.5, 0.8, 0.3],  # wood -> [wood, stone, iron, gold]
        [2.0, 1.0, 1.5, 0.5],  # stone -> [wood, stone, iron, gold] (high rates for stone)
        [1.0, 0.3, 1.0, 2.0],  # iron -> [wood, stone, iron, gold] (good gold rate)
        [3.0, 2.0, 1.5, 1.0]   # gold -> [wood, stone, iron, gold]
    ])
    
    # Agent C: Wants wood, has gold
    # - Will trade gold for wood at rate 1:3 (very good for wood)
    # - Will trade gold for stone at rate 1:2
    agent_c.trading_matrix = np.array([
        [1.0, 0.8, 0.5, 0.2],  # wood -> [wood, stone, iron, gold] (low rates, wants wood)
        [1.5, 1.0, 0.8, 0.3],  # stone -> [wood, stone, iron, gold]
        [2.0, 1.2, 1.0, 0.4],  # iron -> [wood, stone, iron, gold]
        [3.0, 2.0, 1.5, 1.0]   # gold -> [wood, stone, iron, gold] (good rates for everything)
    ])
    
    return [agent_a, agent_b, agent_c]


def demonstrate_strategic_value():
    """Demonstrate how strategic value calculation works."""
    print("🏪 Strategic Value Function Demonstration")
    print("=" * 60)
    
    agents = create_example_scenario()
    agent_a, agent_b, agent_c = agents
    
    # Create market data
    market_data = {
        agent.agent_id: agent.trading_matrix for agent in agents
    }
    
    print("\n📋 Scenario Setup:")
    print(f"Agent A: Wants GOLD, has {agent_a.inventory}")
    print(f"Agent B: Wants STONE, has {agent_b.inventory}")
    print(f"Agent C: Wants WOOD, has {agent_c.inventory}")
    
    print("\n🔄 Trading Opportunities:")
    print("Direct path for Agent A (wood → gold): Very poor rates")
    print("Indirect path for Agent A: wood → iron (via B) → gold (via C)")
    print("This creates strategic value for iron and stone in Agent A's inventory")
    
    print("\n💰 Value Calculations:")
    
    for agent in agents:
        print(f"\n🤖 {agent.agent_id.upper()} (wants {agent.desired_item}):")
        
        # Calculate reward without strategic value (old method)
        basic_reward = agent.inventory[agent.desired_item]
        print(f"  Basic reward (desired item only): {basic_reward:.2f}")
        
        # Calculate reward with strategic value (new method)
        total_reward = agent.calculate_reward(market_data)
        strategic_component = total_reward - basic_reward
        print(f"  Total reward (with strategic value): {total_reward:.2f}")
        print(f"  Strategic value component: {strategic_component:.2f}")
        
        # Show strategic value breakdown by item
        print("  Strategic value by item:")
        desired_item_idx = agent.items_list.index(agent.desired_item)
        
        for item_idx, item in enumerate(agent.items_list):
            if item == agent.desired_item or agent.inventory[item] <= 0:
                continue
                
            best_rate = agent._find_best_conversion_path(
                item_idx, desired_item_idx, market_data, max_hops=3
            )
            quantity = agent.inventory[item]
            strategic_val = quantity * best_rate * 0.3  # discount factor
            
            print(f"    {item}: {quantity} units × {best_rate:.3f} rate = {strategic_val:.2f}")
    
    print("\n🎯 Key Insights:")
    print("1. Agent A values wood not just for direct gold trades (poor rate)")
    print("2. But also for indirect paths: wood → iron → gold (better overall rate)")
    print("3. This encourages agents to collect 'intermediate' items")
    print("4. Creates more complex, realistic trading strategies")
    print("5. Agents learn to position themselves in trading networks")


def demonstrate_path_finding():
    """Demonstrate the path-finding algorithm."""
    print("\n\n🔍 Path-Finding Algorithm Demonstration")
    print("=" * 60)
    
    agents = create_example_scenario()
    agent_a = agents[0]  # Wants gold, has wood
    
    market_data = {agent.agent_id: agent.trading_matrix for agent in agents}
    
    wood_idx = agent_a.items_list.index('wood')
    gold_idx = agent_a.items_list.index('gold')
    
    print(f"\nFinding best path from WOOD to GOLD for Agent A:")
    print(f"Available agents: {list(market_data.keys())}")
    
    # Demonstrate path finding with different hop limits
    for max_hops in [1, 2, 3]:
        best_rate = agent_a._find_best_conversion_path(
            wood_idx, gold_idx, market_data, max_hops=max_hops
        )
        print(f"  Max {max_hops} hop{'s' if max_hops > 1 else ''}: {best_rate:.4f} gold per wood")
    
    print(f"\nThis shows how multi-hop trading can find better conversion rates!")
    print(f"The algorithm considers all possible trading chains up to the hop limit.")


if __name__ == "__main__":
    demonstrate_strategic_value()
    demonstrate_path_finding()
    
    print("\n" + "=" * 60)
    print("🎉 Strategic Value Function Demo Complete!")
    print("Run the main training to see this in action with learning agents.")
    print("=" * 60)
