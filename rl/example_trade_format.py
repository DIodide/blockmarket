#!/usr/bin/env python3
"""
Example demonstrating the new trade request format and validation.

This script shows how the new format (b_i, b_j, D_i, D_j, D_j_amt) works
and how invalid trade requests are filtered out.
"""

import numpy as np
from agent import TradingAgent
from environment import TradingEnvironment
from config import load_config


def create_example_scenario():
    """Create a scenario to demonstrate trade request validation."""
    config = load_config()
    
    # Override config for this example
    config['environment']['items_list'] = ['wood', 'stone', 'iron']
    config['environment']['population_size'] = 3
    
    env = TradingEnvironment(config)
    
    # Create three agents manually with specific inventories
    agent_a = TradingAgent('agent_a', config, env.items_list, 'iron',
                          initial_inventory={'wood': 5, 'stone': 0, 'iron': 0})
    
    agent_b = TradingAgent('agent_b', config, env.items_list, 'wood',
                          initial_inventory={'wood': 0, 'stone': 8, 'iron': 3})
    
    agent_c = TradingAgent('agent_c', config, env.items_list, 'stone',
                          initial_inventory={'wood': 2, 'stone': 0, 'iron': 1})
    
    # Set up trading matrices
    # Agent A: Wants iron, has wood
    # Will trade 2 wood for 1 iron, 1 wood for 1 stone
    agent_a.trading_matrix = np.array([
        [1.0, 1.0, 0.5],  # wood -> [wood, stone, iron]
        [1.0, 1.0, 0.3],  # stone -> [wood, stone, iron]
        [2.0, 3.0, 1.0]   # iron -> [wood, stone, iron]
    ])
    
    # Agent B: Wants wood, has stone and iron
    # Will trade 1 stone for 2 wood, 1 iron for 3 wood
    agent_b.trading_matrix = np.array([
        [1.0, 0.5, 0.3],  # wood -> [wood, stone, iron]
        [2.0, 1.0, 0.5],  # stone -> [wood, stone, iron]
        [3.0, 2.0, 1.0]   # iron -> [wood, stone, iron]
    ])
    
    # Agent C: Wants stone, has wood and iron
    # Will trade 1 wood for 1 stone, 1 iron for 2 stone
    agent_c.trading_matrix = np.array([
        [1.0, 1.0, 0.5],  # wood -> [wood, stone, iron]
        [1.0, 1.0, 0.8],  # stone -> [wood, stone, iron]
        [0.5, 2.0, 1.0]   # iron -> [wood, stone, iron]
    ])
    
    env.agents = [agent_a, agent_b, agent_c]
    
    # Update positions and market data
    for agent in env.agents:
        env.agent_positions[agent.agent_id] = agent.position
    
    return env


def demonstrate_trade_requests():
    """Demonstrate trade request generation and validation."""
    print("🔄 Trade Request Format Demonstration")
    print("=" * 60)
    
    env = create_example_scenario()
    
    print("\n📋 Initial Setup:")
    for agent in env.agents:
        print(f"{agent.agent_id}: wants {agent.desired_item}, has {agent.inventory}")
    
    print("\n🔄 Trade Request Process:")
    
    # Phase 1: Update trading matrices
    env._update_trading_matrices()
    print("✅ Phase 1: Trading matrices updated")
    
    # Phase 2: Collect market data
    env._collect_market_data()
    print("✅ Phase 2: Market data collected")
    
    # Phase 3: Generate trade requests
    print("\n📝 Phase 3: Generating Trade Requests")
    print("Format: (b_i, b_j, D_i, D_j, D_j_amt)")
    print("  b_i = requester ID")
    print("  b_j = target ID") 
    print("  D_i = item giving")
    print("  D_j = item wanting")
    print("  D_j_amt = amount wanting")
    
    trade_requests = []
    
    for agent in env.agents:
        print(f"\n🤖 {agent.agent_id} (wants {agent.desired_item}):")
        
        trade_action = agent.select_trade_action(env.market_data, env.agent_positions)
        
        if trade_action is not None:
            target_id, item_giving, item_wanting, amount_wanting = trade_action
            print(f"  Proposed trade: give {item_giving} to {target_id} for {amount_wanting:.2f} {item_wanting}")
            
            # Validate the trade request
            is_valid = env._validate_trade_request(agent, target_id, item_giving, item_wanting, amount_wanting)
            
            if is_valid:
                trade_requests.append((agent.agent_id, target_id, item_giving, item_wanting, amount_wanting))
                print(f"  ✅ VALID: Request added to trade list")
            else:
                print(f"  ❌ INVALID: Insufficient resources or target unwilling")
                
                # Show why it's invalid
                target_agent = next((a for a in env.agents if a.agent_id == target_id), None)
                if target_agent:
                    print(f"    Requester has {agent.inventory[item_giving]:.2f} {item_giving}")
                    print(f"    Target has {target_agent.inventory[item_wanting]:.2f} {item_wanting}")
                    
                    # Check target's willingness
                    item_giving_idx = env.items_list.index(item_giving)
                    item_wanting_idx = env.items_list.index(item_wanting)
                    target_rate = target_agent.trading_matrix[item_wanting_idx, item_giving_idx]
                    required_giving = amount_wanting / target_rate if target_rate > 0 else float('inf')
                    
                    print(f"    Target rate: {target_rate:.3f} {item_giving} per {item_wanting}")
                    print(f"    Required giving: {required_giving:.2f} {item_giving}")
        else:
            print(f"  No trade action selected")
    
    print(f"\n📊 Summary:")
    print(f"Valid trade requests: {len(trade_requests)}")
    
    if trade_requests:
        print("\n🔄 Valid Trade Requests:")
        for i, (req_id, tgt_id, give_item, want_item, want_amt) in enumerate(trade_requests, 1):
            print(f"  {i}. {req_id} → {tgt_id}: {give_item} for {want_amt:.2f} {want_item}")
    
    return trade_requests


def demonstrate_trade_execution():
    """Demonstrate trade execution with the new format."""
    print("\n\n⚡ Trade Execution Demonstration")
    print("=" * 60)
    
    env = create_example_scenario()
    
    # Set up a specific scenario
    # Agent A has 5 wood, wants iron
    # Agent B has 3 iron, wants wood, rate: 1 iron = 3 wood
    
    print("📋 Scenario Setup:")
    print("Agent A: has 5 wood, wants iron")
    print("Agent B: has 3 iron, wants wood")
    print("Agent B's rate: 1 iron = 3 wood")
    
    # Create a manual trade request
    trade_request = ('agent_a', 'agent_b', 'wood', 'iron', 1.0)  # A wants 1 iron from B
    
    print(f"\n🔄 Trade Request: {trade_request}")
    print("Format: (requester, target, giving, wanting, amount_wanting)")
    
    # Execute the trade
    env._update_trading_matrices()
    env._collect_market_data()
    
    print("\n⚡ Executing Trade:")
    
    # Show before state
    agent_a = env.agents[0]
    agent_b = env.agents[1]
    
    print("Before trade:")
    print(f"  Agent A: {agent_a.inventory}")
    print(f"  Agent B: {agent_b.inventory}")
    
    # Execute trade
    trade_result = env._try_execute_trade(trade_request)
    
    if trade_result:
        print("\n✅ Trade executed successfully!")
        print(f"Trade details: {trade_result}")
        
        print("\nAfter trade:")
        print(f"  Agent A: {agent_a.inventory}")
        print(f"  Agent B: {agent_b.inventory}")
        
        # Verify the trade
        gave = trade_result['requester_gave']
        received = trade_result['requester_received']
        print(f"\nVerification:")
        print(f"  Agent A gave: {gave[1]:.2f} {gave[0]}")
        print(f"  Agent A received: {received[1]:.2f} {received[0]}")
        
    else:
        print("❌ Trade failed!")


def demonstrate_invalid_scenarios():
    """Demonstrate various invalid trade scenarios."""
    print("\n\n❌ Invalid Trade Scenarios")
    print("=" * 60)
    
    env = create_example_scenario()
    env._update_trading_matrices()
    env._collect_market_data()
    
    agent_a = env.agents[0]  # has 5 wood
    agent_b = env.agents[1]  # has 8 stone, 3 iron
    
    invalid_scenarios = [
        # Scenario 1: Requester doesn't have enough of giving item
        ('agent_a', 'agent_b', 'stone', 'iron', 1.0, "Requester doesn't have stone"),
        
        # Scenario 2: Target doesn't have enough of wanting item
        ('agent_a', 'agent_b', 'wood', 'iron', 5.0, "Target doesn't have 5 iron"),
        
        # Scenario 3: Requester can't afford the trade
        ('agent_a', 'agent_b', 'wood', 'iron', 2.0, "Requester can't afford 2 iron (needs 6 wood)"),
        
        # Scenario 4: Target unwilling (rate = 0)
        ('agent_a', 'agent_c', 'stone', 'wood', 1.0, "Requester doesn't have stone to give"),
    ]
    
    for i, (req_id, tgt_id, give_item, want_item, want_amt, reason) in enumerate(invalid_scenarios, 1):
        print(f"\n{i}. Testing: {req_id} wants {want_amt} {want_item} from {tgt_id} for {give_item}")
        print(f"   Expected issue: {reason}")
        
        requester = next(a for a in env.agents if a.agent_id == req_id)
        is_valid = env._validate_trade_request(requester, tgt_id, give_item, want_item, want_amt)
        
        if is_valid:
            print("   ❌ UNEXPECTED: Trade was marked as valid!")
        else:
            print("   ✅ CORRECT: Trade correctly identified as invalid")


if __name__ == "__main__":
    demonstrate_trade_requests()
    demonstrate_trade_execution()
    demonstrate_invalid_scenarios()
    
    print("\n" + "=" * 60)
    print("🎉 Trade Request Format Demo Complete!")
    print("Key improvements:")
    print("- Clear specification of what each agent gives and wants")
    print("- Validation prevents impossible trades")
    print("- Agents can't trade what they don't have")
    print("- More realistic trading mechanics")
    print("=" * 60)
