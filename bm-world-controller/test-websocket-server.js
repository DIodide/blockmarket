const WebSocket = require('ws');

// Create WebSocket server
const wss = new WebSocket.Server({ port: 8080 });

console.log('WebSocket server started on port 8080');

wss.on('connection', function connection(ws) {
    console.log('Client connected');
    
    // Send welcome message
    ws.send('say Welcome to BlockMarket WebSocket Server!');
    
    // Send a test command after 3 seconds
    setTimeout(() => {
        ws.send('say This is a test command from WebSocket server');
    }, 3000);
    
    // Send another test command after 6 seconds
    setTimeout(() => {
        ws.send('give @a diamond 1');
    }, 6000);
    
    // Handle incoming messages from client
    ws.on('message', function incoming(message) {
        console.log('Received from client:', message.toString());
        
        // Echo the message back
        ws.send(`say Echo: ${message.toString()}`);
    });
    
    ws.on('close', function close() {
        console.log('Client disconnected');
    });
    
    ws.on('error', function error(err) {
        console.error('WebSocket error:', err);
    });
});

// Handle server errors
wss.on('error', function error(err) {
    console.error('Server error:', err);
});

console.log('WebSocket server is ready. Connect your Minecraft plugin to ws://localhost:8080');
console.log('Test commands will be sent automatically.');
