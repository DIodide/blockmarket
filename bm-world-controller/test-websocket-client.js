/**
 * Test WebSocket Client for BlockMarket World Controller
 * 
 * This client connects to the Minecraft WebSocket server and tests trading floor creation
 * Usage: node test-websocket-client.js [server-url]
 */

const WebSocket = require('ws');

// Configuration
const WEBSOCKET_URL = process.argv[2] || 'wss://localhost:8080';

console.log('🚀 BlockMarket WebSocket Test Client');
console.log(`🔗 Connecting to: ${WEBSOCKET_URL}`);

// Test scenarios
const testScenarios = [
    {
        name: "Server Info Request",
        delay: 1000,
        message: {
            type: "get_server_info"
        }
    },
    {
        name: "Ping Test",
        delay: 2000,
        message: {
            type: "ping",
            timestamp: Date.now()
        }
    },
    {
        name: "Default 10x10 Trading Floor",
        delay: 3000,
        message: {
            type: "create_trading_floor",
            size: 10
        }
    },
    {
        name: "Small 5x5 Trading Floor at Spawn",
        delay: 8000,
        message: {
            type: "create_trading_floor",
            size: 5,
            world: "world"
        }
    },
    {
        name: "Medium 15x15 Trading Floor at Custom Location",
        delay: 13000,
        message: {
            type: "create_trading_floor",
            size: 15,
            centerX: 200,
            centerZ: 300,
            world: "world"
        }
    },
    {
        name: "Broadcast Message Test",
        delay: 18000,
        message: {
            type: "broadcast",
            message: "Hello from test client! Trading floors are being created."
        }
    },
    {
        name: "Invalid Size Test (should fail)",
        delay: 20000,
        message: {
            type: "create_trading_floor",
            size: 150  // Too large, should be rejected
        }
    }
];

// Stats tracking
let messagesReceived = 0;
let testsPassed = 0;
let testsFailed = 0;

function logMessage(emoji, message) {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`${timestamp} ${emoji} ${message}`);
}

function runTest(ws, scenario) {
    setTimeout(() => {
        logMessage('🧪', `Running: ${scenario.name}`);
        logMessage('📤', `Sending: ${JSON.stringify(scenario.message, null, 2)}`);
        ws.send(JSON.stringify(scenario.message));
    }, scenario.delay);
}

const ws = new WebSocket(WEBSOCKET_URL);

ws.on('open', () => {
    logMessage('✅', 'Connected to WebSocket server');
    
    // Run all test scenarios
    testScenarios.forEach(scenario => {
        runTest(ws, scenario);
    });
    
    // Close connection after all tests
    setTimeout(() => {
        logMessage('👋', 'All tests completed, closing connection');
        ws.close();
    }, 25000);
});

ws.on('message', (data) => {
    messagesReceived++;
    try {
        const message = JSON.parse(data.toString());
        
        switch (message.type) {
            case 'welcome':
                logMessage('🎉', `Welcome received: ${message.message} (Client ID: ${message.clientId})`);
                testsPassed++;
                break;
                
            case 'trading_floor_created':
                logMessage('🏢', `Trading floor created successfully!`);
                logMessage('📍', `Center: (${message.centerX}, ${message.centerY}, ${message.centerZ}), Size: ${message.size}x${message.size}, World: ${message.world}`);
                testsPassed++;
                break;
                
            case 'trading_floor_created_broadcast':
                logMessage('📢', `Someone else created a trading floor: ${message.size}x${message.size} at (${message.centerX}, ${message.centerY}, ${message.centerZ}) by ${message.createdBy}`);
                break;
                
            case 'server_info':
                logMessage('🖥️', `Server Info - Name: ${message.serverName}, Version: ${message.version}`);
                logMessage('👥', `Players: ${message.onlinePlayers}/${message.maxPlayers}, WebSocket Clients: ${message.connectedClients}`);
                testsPassed++;
                break;
                
            case 'pong':
                const latency = Date.now() - message.clientTimestamp;
                logMessage('🏓', `Pong received! Latency: ${latency}ms`);
                testsPassed++;
                break;
                
            case 'broadcast_message':
                logMessage('📻', `Broadcast from ${message.from}: ${message.message}`);
                break;
                
            case 'client_connected':
                logMessage('👋', `Another client connected: ${message.clientId}`);
                break;
                
            case 'client_disconnected':
                logMessage('👋', `Another client disconnected: ${message.clientId}`);
                break;
                
            case 'error':
                logMessage('❌', `Error: ${message.message}`);
                testsFailed++;
                break;
                
            case 'echo':
                logMessage('🔄', `Echo: ${message.originalMessage}`);
                testsPassed++;
                break;
                
            default:
                logMessage('❓', `Unknown message type: ${message.type}`);
                logMessage('📥', JSON.stringify(message, null, 2));
                break;
        }
        
    } catch (e) {
        // Handle non-JSON messages
        logMessage('📥', `Non-JSON message: ${data.toString()}`);
    }
});

ws.on('error', (error) => {
    logMessage('❌', `WebSocket error: ${error.message}`);
});

ws.on('close', (code, reason) => {
    logMessage('🔌', `Connection closed (Code: ${code}, Reason: ${reason})`);
    
    // Print summary
    console.log('\n' + '='.repeat(50));
    console.log('📊 Test Summary:');
    console.log(`📬 Messages Received: ${messagesReceived}`);
    console.log(`✅ Tests Passed: ${testsPassed}`);
    console.log(`❌ Tests Failed: ${testsFailed}`);
    console.log(`🎯 Success Rate: ${testsPassed + testsFailed > 0 ? Math.round((testsPassed / (testsPassed + testsFailed)) * 100) : 0}%`);
    console.log('='.repeat(50));
    
    process.exit(0);
});

// Handle process termination
process.on('SIGINT', () => {
    logMessage('⚠️', 'Received SIGINT, closing connection...');
    ws.close();
});
