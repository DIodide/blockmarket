#!/usr/bin/env python3
"""
Convenience script to run the trading environment in different modes.
"""

import subprocess
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description='Run Multi-Agent Trading Environment')
    parser.add_argument('--mode', choices=['training', 'unified', 'socket-only'], 
                       default='unified', help='Run mode')
    parser.add_argument('--no-web', action='store_true', help='Disable web interface')
    parser.add_argument('--no-training', action='store_true', help='Disable training')
    parser.add_argument('--no-socket', action='store_true', help='Disable socket client')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', default='config.yaml', help='Config file')
    
    args = parser.parse_args()
    
    # Build command
    cmd = [sys.executable, 'main.py']
    cmd.extend(['--mode', args.mode])
    cmd.extend(['--config', args.config])
    
    if args.no_web:
        cmd.append('--no-web')
    if args.no_training:
        cmd.append('--no-training')
    if args.no_socket:
        cmd.append('--no-socket')
    if args.debug:
        cmd.append('--debug')
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    # Show mode-specific information
    if args.mode == 'unified':
        print("🏪 UNIFIED MODE")
        print("This mode runs:")
        if not args.no_web:
            print("  ✅ Flask web server (visualization)")
        else:
            print("  ❌ Flask web server (disabled)")
        
        if not args.no_socket:
            print("  ✅ Socket.IO client (external simulation control)")
        else:
            print("  ❌ Socket.IO client (disabled)")
        
        if not args.no_training:
            print("  ✅ Internal training loop")
        else:
            print("  ❌ Internal training loop (disabled)")
        print()
        
    elif args.mode == 'training':
        print("🎯 TRAINING MODE")
        print("This mode runs the original training-only environment")
        if not args.no_web:
            print("  ✅ Flask web server (visualization)")
        print("  ✅ Internal training loop")
        print()
        
    elif args.mode == 'socket-only':
        print("🔌 SOCKET-ONLY MODE")
        print("This mode only runs the Socket.IO client")
        print("  ✅ Socket.IO client (waits for external commands)")
        print()
    
    # Run the command
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Process failed with exit code {e.returncode}")
        return e.returncode
    
    return 0


if __name__ == "__main__":
    exit(main())