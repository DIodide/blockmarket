# BlockMarket World Controller

A Minecraft plugin that connects to a WebSocket server and executes commands in the Minecraft server based on messages received from the WebSocket.

## Features

- **WebSocket Integration**: Connects to a WebSocket server and receives messages
- **Command Execution**: Safely executes Minecraft commands from WebSocket messages
- **Security**: Built-in command filtering and validation
- **Auto-reconnection**: Automatically reconnects to WebSocket server on connection loss
- **Configuration**: Highly configurable through config.yml
- **Logging**: Comprehensive logging for debugging and monitoring

## Installation

1. Build the plugin using Maven:
   ```bash
   mvn clean package
   ```

2. Copy the generated JAR file from `target/bm-world-controller-0.1-SNAPSHOT.jar` to your Minecraft server's `plugins` folder

3. Start your Minecraft server

4. Configure the plugin by editing `plugins/bm-world-controller/config.yml`

## Configuration

The plugin creates a `config.yml` file with the following settings:

### WebSocket Configuration
```yaml
websocket:
  server-url: "ws://localhost:8080/websocket"  # WebSocket server URL
  auto-reconnect: true                          # Auto-reconnect on disconnect
  max-reconnect-attempts: 5                     # Max reconnection attempts
  reconnect-delay: 5                            # Delay between attempts (seconds)
```

### Command Security
```yaml
commands:
  allowed-commands:                             # Whitelist of allowed commands
    - "say"
    - "give"
    - "tp"
    # ... more commands
  
  blocked-commands:                             # Blacklist of blocked commands
    - "stop"
    - "ban"
    - "kick"
    # ... more commands
```

### Security Settings
```yaml
security:
  validate-commands: true                       # Validate command syntax
  max-command-length: 256                       # Maximum command length
  strip-color-codes: true                      # Remove color codes from commands
```

## Testing

### Test WebSocket Server

A simple test WebSocket server is included (`test-websocket-server.js`). To use it:

1. Install Node.js and npm
2. Install WebSocket dependency:
   ```bash
   npm install ws
   ```
3. Run the test server:
   ```bash
   node test-websocket-server.js
   ```

The test server will:
- Start on port 8080
- Send test commands to connected clients
- Echo back any messages received

### Manual Testing

1. Start your Minecraft server with the plugin installed
2. Run the test WebSocket server
3. Check the Minecraft server console for connection messages
4. Observe the test commands being executed in-game

## Message Format

The plugin expects simple text messages from the WebSocket server. Commands should be sent as plain text:

- `say Hello World!` - Broadcasts a message
- `give @a diamond 1` - Gives all players a diamond
- `tp @a 0 100 0` - Teleports all players to coordinates
- `weather clear` - Changes weather to clear

## Security Features

- **Command Whitelist/Blacklist**: Control which commands can be executed
- **Dangerous Command Blocking**: Automatically blocks potentially harmful commands
- **Command Validation**: Validates command syntax before execution
- **Length Limits**: Prevents excessively long commands
- **Color Code Stripping**: Removes color codes to prevent formatting attacks

## Logging

The plugin provides comprehensive logging:

- WebSocket connection status
- Received messages
- Command execution results
- Error messages and stack traces

Check your server console or log files for detailed information.

## Troubleshooting

### WebSocket Connection Issues
- Verify the WebSocket server URL in config.yml
- Ensure the WebSocket server is running and accessible
- Check firewall settings

### Command Execution Issues
- Verify the command is in the allowed list (if using whitelist)
- Check that the command is not in the blocked list
- Ensure the command syntax is correct

### Plugin Not Loading
- Verify you're using a compatible Minecraft server (Paper/Spigot 1.20+)
- Check that all dependencies are properly included
- Review server logs for error messages

## API

The plugin provides a simple API for other plugins:

```java
// Get the plugin instance
BmWorldController plugin = (BmWorldController) Bukkit.getPluginManager().getPlugin("bm-world-controller");

// Check WebSocket connection status
boolean connected = plugin.isWebSocketConnected();

// Send a message to the WebSocket server
plugin.sendWebSocketMessage("Hello from Minecraft!");

// Get the command executor
CommandExecutor executor = plugin.getCommandExecutor();
```

## Development

### Building from Source

1. Clone the repository
2. Install Maven
3. Run: `mvn clean package`
4. Find the JAR in the `target` directory

### Dependencies

- Java 21+
- Paper API 1.20.6+
- Java-WebSocket 1.5.4

## License

This project is licensed under the MIT License - see the LICENSE file for details.
