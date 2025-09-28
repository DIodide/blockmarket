#!/usr/bin/env python3
"""
Debug script to test Socket.IO connection and event reception.
"""

import socketio
import logging
import time
import json

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_socket_connection():
    """Test basic Socket.IO connection and event handling."""
    
    url = 'https://geographical-clonic-jimena.ngrok-free.dev'  # Base URL without /model
    
    print("🔍 Socket.IO Connection Debug Test")
    print("=" * 50)
    print(f"Target URL: {url}")
    print()
    
    # Create client with verbose logging
    sio = socketio.Client(
        logger=True,
        engineio_logger=True,
        reconnection=True,
        reconnection_attempts=3,
        reconnection_delay=2
    )
    
    # Event counters
    events_received = {
        'connect': 0,
        'disconnect': 0,
        'start_simulation': 0,
        'other': 0
    }
    
    @sio.event(namespace='/model')
    def connect():
        logger.info("🎉 CONNECTED to /model namespace successfully!")
        events_received['connect'] += 1
        print(f"✅ /model namespace connection established at {time.strftime('%H:%M:%S')}")
        
    @sio.event(namespace='/model')
    def connect_error(data):
        logger.error(f"❌ /model namespace connection error: {data}")
        print(f"❌ /model namespace connection failed: {data}")
        
    @sio.event(namespace='/model')
    def disconnect():
        logger.info("🔌 Disconnected from /model namespace")
        events_received['disconnect'] += 1
        print(f"🔌 Disconnected from /model namespace at {time.strftime('%H:%M:%S')}")
        
    @sio.event(namespace='/model')
    def start_simulation(data):
        logger.info("🚀 RECEIVED start_simulation event from /model namespace!")
        events_received['start_simulation'] += 1
        print(f"🚀 start_simulation received at {time.strftime('%H:%M:%S')}")
        print(f"📊 Data type: {type(data)}")
        print(f"📊 Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        if isinstance(data, dict) and 'botInventoryMap' in data:
            bot_count = len(data['botInventoryMap'])
            print(f"🤖 Bot count: {bot_count}")
            print(f"🤖 Bot keys: {list(data['botInventoryMap'].keys())}")
        
    # Catch-all for any other events in /model namespace
    @sio.event(namespace='/model')
    def catch_all(event, *args):
        logger.info(f"🔍 /model Event '{event}' received with {len(args)} args")
        events_received['other'] += 1
        print(f"🔍 /model Event: {event}, Args: {args}")
    
    try:
        print("🔌 Attempting connection...")
        
        # Add ngrok headers
        headers = {'ngrok-skip-browser-warning': 'true'}
        
        sio.connect(
            url,
            headers=headers,
            transports=['websocket', 'polling'],
            wait_timeout=15,
            namespaces=['/model']
        )
        
        print(f"🎯 Connection status: {'Connected' if sio.connected else 'Failed'}")
        
        if sio.connected:
            print("✅ Connection successful!")
            print("⏳ Waiting for events (60 seconds)...")
            print("   - Listening for 'start_simulation' events")
            print("   - Press Ctrl+C to stop")
            
            # Wait for events
            start_time = time.time()
            while time.time() - start_time < 60:
                time.sleep(1)
                
                # Print status every 10 seconds
                if int(time.time() - start_time) % 10 == 0:
                    elapsed = int(time.time() - start_time)
                    print(f"⏱️  {elapsed}s elapsed - Events: {sum(events_received.values())}")
                    
        else:
            print("❌ Connection failed!")
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    finally:
        if sio.connected:
            sio.disconnect()
            
        print("\n📊 Final Results:")
        print(f"   Connect events: {events_received['connect']}")
        print(f"   Disconnect events: {events_received['disconnect']}")
        print(f"   start_simulation events: {events_received['start_simulation']}")
        print(f"   Other events: {events_received['other']}")
        print(f"   Total events: {sum(events_received.values())}")
        
        if events_received['start_simulation'] > 0:
            print("🎉 SUCCESS: start_simulation events were received!")
        elif events_received['connect'] > 0:
            print("⚠️  Connected but no start_simulation events received")
            print("   - Check if server is sending the events")
            print("   - Verify event name spelling")
        else:
            print("❌ FAILED: Could not connect to server")
            print("   - Check URL is correct")
            print("   - Check server is running")
            print("   - Check network connectivity")


if __name__ == "__main__":
    test_socket_connection()
