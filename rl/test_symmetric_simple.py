#!/usr/bin/env python3
"""
Simple test script to verify the symmetric inverse trading matrix property.
"""

import numpy as np
from agent import TradingAgent
from config import load_config


def test_symmetric_property():
    """Test that trading matrices maintain the symmetric inverse property."""
    print("Testing Symmetric Inverse Trading Matrix Property")
    print("=" * 60)
    
    config = load_config()
    items_list = ['wood', 'stone', 'iron', 'gold', 'food']
    
    # Create a test agent
    agent = TradingAgent('test_agent', config, items_list, 'gold')
    
    print("Agent created successfully")
    print(f"Trading matrix shape: {agent.trading_matrix.shape}")
    
    # Test initial matrix property
    print("\nTesting Initial Matrix Property:")
    matrix = agent.trading_matrix
    
    symmetric_violations = 0
    diagonal_violations = 0
    
    for i in range(len(items_list)):
        for j in range(len(items_list)):
            if i == j:  # Check diagonal
                if matrix[i, j] != 1.0:
                    diagonal_violations += 1
                    print(f"DIAGONAL VIOLATION: matrix[{i},{j}]={matrix[i,j]:.4f}, expected=1.0")
            else:  # Check symmetric inverse property
                expected_inverse = 1.0 / matrix[i, j]
                actual_inverse = matrix[j, i]
                
                if not np.isclose(expected_inverse, actual_inverse, rtol=1e-10):
                    symmetric_violations += 1
                    print(f"SYMMETRY VIOLATION: matrix[{i},{j}]={matrix[i,j]:.4f}, "
                          f"matrix[{j},{i}]={matrix[j,i]:.4f}, "
                          f"expected={expected_inverse:.4f}")
    
    if symmetric_violations == 0 and diagonal_violations == 0:
        print("SUCCESS: Initial matrix satisfies all constraints!")
    else:
        if symmetric_violations > 0:
            print(f"ERROR: Found {symmetric_violations} symmetric violations in initial matrix")
        if diagonal_violations > 0:
            print(f"ERROR: Found {diagonal_violations} diagonal violations in initial matrix")
    
    # Test matrix after update
    print("\nTesting Matrix After Neural Network Update:")
    
    # Simulate a neural network update
    agent.update_trading_matrix()
    matrix_after_update = agent.trading_matrix
    
    symmetric_violations = 0
    diagonal_violations = 0
    
    for i in range(len(items_list)):
        for j in range(len(items_list)):
            if i == j:  # Check diagonal
                if matrix_after_update[i, j] != 1.0:
                    diagonal_violations += 1
                    print(f"DIAGONAL VIOLATION: matrix[{i},{j}]={matrix_after_update[i,j]:.4f}, expected=1.0")
            else:  # Check symmetric inverse property
                expected_inverse = 1.0 / matrix_after_update[i, j]
                actual_inverse = matrix_after_update[j, i]
                
                if not np.isclose(expected_inverse, actual_inverse, rtol=1e-10):
                    symmetric_violations += 1
                    print(f"SYMMETRY VIOLATION: matrix[{i},{j}]={matrix_after_update[i,j]:.4f}, "
                          f"matrix[{j},{i}]={matrix_after_update[j,i]:.4f}, "
                          f"expected={expected_inverse:.4f}")
    
    if symmetric_violations == 0 and diagonal_violations == 0:
        print("SUCCESS: Matrix after update satisfies all constraints!")
    else:
        if symmetric_violations > 0:
            print(f"ERROR: Found {symmetric_violations} symmetric violations after update")
        if diagonal_violations > 0:
            print(f"ERROR: Found {diagonal_violations} diagonal violations after update")
    
    # Test matrix after mutation
    print("\nTesting Matrix After Mutation:")
    
    original_matrix = agent.trading_matrix.copy()
    agent.mutate(mutation_rate=1.0)  # Force mutation
    matrix_after_mutation = agent.trading_matrix
    
    symmetric_violations = 0
    diagonal_violations = 0
    
    for i in range(len(items_list)):
        for j in range(len(items_list)):
            if i == j:  # Check diagonal
                if matrix_after_mutation[i, j] != 1.0:
                    diagonal_violations += 1
                    print(f"DIAGONAL VIOLATION: matrix[{i},{j}]={matrix_after_mutation[i,j]:.4f}, expected=1.0")
            else:  # Check symmetric inverse property
                expected_inverse = 1.0 / matrix_after_mutation[i, j]
                actual_inverse = matrix_after_mutation[j, i]
                
                if not np.isclose(expected_inverse, actual_inverse, rtol=1e-10):
                    symmetric_violations += 1
                    print(f"SYMMETRY VIOLATION: matrix[{i},{j}]={matrix_after_mutation[i,j]:.4f}, "
                          f"matrix[{j},{i}]={matrix_after_mutation[j,i]:.4f}, "
                          f"expected={expected_inverse:.4f}")
    
    if symmetric_violations == 0 and diagonal_violations == 0:
        print("SUCCESS: Matrix after mutation satisfies all constraints!")
    else:
        if symmetric_violations > 0:
            print(f"ERROR: Found {symmetric_violations} symmetric violations after mutation")
        if diagonal_violations > 0:
            print(f"ERROR: Found {diagonal_violations} diagonal violations after mutation")
    
    # Show example of the property
    print("\nExample Trading Rates:")
    print("Items:", items_list)
    print("\nTrading Matrix (how much of column item for 1 unit of row item):")
    
    # Print matrix with labels
    print("     ", end="")
    for item in items_list:
        print(f"{item[:4]:>6}", end="")
    print()
    
    for i, item in enumerate(items_list):
        print(f"{item[:4]:>4} ", end="")
        for j in range(len(items_list)):
            print(f"{matrix_after_mutation[i,j]:6.3f}", end="")
        print()
    
    print(f"\nExample: If 1 {items_list[0]} = {matrix_after_mutation[0,1]:.3f} {items_list[1]}")
    print(f"         Then 1 {items_list[1]} = {matrix_after_mutation[1,0]:.3f} {items_list[0]}")
    print(f"         Verification: {matrix_after_mutation[0,1]:.3f} x {matrix_after_mutation[1,0]:.3f} = {matrix_after_mutation[0,1] * matrix_after_mutation[1,0]:.6f} (should be 1.0)")
    
    return symmetric_violations == 0 and diagonal_violations == 0


if __name__ == "__main__":
    success = test_symmetric_property()
    
    print("\n" + "=" * 60)
    if success:
        print("TRADING MATRIX CONSTRAINTS TEST PASSED!")
        print("The trading matrices now maintain perfect consistency:")
        print("- If 1 A trades for X B, then 1 B trades for 1/X A (symmetric inverse)")
        print("- Diagonal elements are ALWAYS 1.0 (item trades for itself)")
        print("- All constraints are preserved through training and mutation")
    else:
        print("TEST FAILED: Matrix constraint violations found!")
    print("=" * 60)
