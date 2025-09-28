#!/usr/bin/env python3
"""
Example usage of the Socket.IO trading simulation client.
"""

import logging
import time
from socket_client import SocketSimulationClient

def main():
    """Example of how to use the socket client."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Socket server URL (adjust as needed)
    socket_url = 'https://geographical-clonic-jimena.ngrok-free.dev/model'
    
    print("🔌 Socket.IO Trading Simulation Client Example")
    print("=" * 50)
    print(f"Connecting to: {socket_url}")
    print()
    
    # Create client
    client = SocketSimulationClient(socket_url)
    
    # Connect to server
    if client.connect():
        print("✅ Connected successfully!")
        print("📡 Waiting for start_simulation command from server...")
        print("   (The server will send bot inventory data)")
        print()
        print("Expected data format:")
        print("""
        {
          "botInventoryMap": {
            "0-0": {"diamond": 5, "gold": 10, "apple": 3, "emerald": 2, "redstone": 8},
            "0-1": {"diamond": 3, "gold": 8, "apple": 5, "emerald": 4, "redstone": 6},
            "1-0": {"diamond": 7, "gold": 6, "apple": 4, "emerald": 3, "redstone": 9}
          }
        }
        """)
        print()
        print("🔄 Once simulation starts, trade data will be emitted back to server")
        print("⏹️  Press Ctrl+C to stop")
        
        try:
            # Keep running until interrupted
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            
        finally:
            client.disconnect()
            print("👋 Disconnected")
            
    else:
        print("❌ Failed to connect to server")
        print("💡 Make sure the Socket.IO server is running:")
        print("   cd rl/")
        print("   npm install")
        print("   npm start")


if __name__ == "__main__":
    main()
