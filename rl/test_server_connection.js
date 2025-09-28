#!/usr/bin/env node
/**
 * Test script to verify that the Express server is properly receiving trade events
 * from the Python socket client.
 */

import { io } from 'socket.io-client';

const SERVER_URL = 'http://localhost:3001';

console.log('🧪 Testing Socket.IO connection to Express server...');

// Connect to /model namespace (where Python client connects)
const modelSocket = io(`${SERVER_URL}/model`, {
    transports: ['websocket', 'polling']
});

modelSocket.on('connect', () => {
    console.log('✅ Connected to /model namespace');
    
    // Send a test trade event
    const testTradeData = {
        timestep: 999,
        generation: 0,
        trades_count: 1,
        trades: [{
            requester_id: 'test_agent_1',
            target_id: 'test_agent_2',
            item_given: 'gold',
            amount_given: 2.5,
            item_received: 'diamond',
            amount_received: 1.0,
            requester_cell: '0-0',
            target_cell: '1-1'
        }]
    };
    
    console.log('📤 Sending test trade data...');
    modelSocket.emit('trade', testTradeData);
    
    // Test other events too
    modelSocket.emit('simulation_started', { agents_count: 2, items: ['gold', 'diamond'] });
    modelSocket.emit('simulation_stopped', {});
    
    // Disconnect after 2 seconds
    setTimeout(() => {
        console.log('🔌 Disconnecting...');
        modelSocket.disconnect();
        process.exit(0);
    }, 2000);
});

modelSocket.on('connect_error', (error) => {
    console.error('❌ Connection error:', error);
    process.exit(1);
});

modelSocket.on('disconnect', () => {
    console.log('🔌 Disconnected from server');
});

// Handle process termination
process.on('SIGINT', () => {
    console.log('\n👋 Shutting down test...');
    modelSocket.disconnect();
    process.exit(0);
});
