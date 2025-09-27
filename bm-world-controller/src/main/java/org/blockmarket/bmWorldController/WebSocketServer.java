package org.blockmarket.bmWorldController;

import org.bukkit.Bukkit;
import org.bukkit.plugin.java.JavaPlugin;
import org.java_websocket.WebSocket;
import org.java_websocket.handshake.ClientHandshake;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonSyntaxException;

import java.net.InetSocketAddress;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Level;

public class WebSocketServer extends org.java_websocket.server.WebSocketServer {
    private final JavaPlugin plugin;
    private final TradingFloorBuilder tradingFloorBuilder;
    private final ConcurrentHashMap<WebSocket, String> connectedClients;
    private final AtomicInteger clientIdCounter;

    public WebSocketServer(JavaPlugin plugin, int port, TradingFloorBuilder tradingFloorBuilder) {
        super(new InetSocketAddress(port));
        this.plugin = plugin;
        this.tradingFloorBuilder = tradingFloorBuilder;
        this.connectedClients = new ConcurrentHashMap<>();
        this.clientIdCounter = new AtomicInteger(1);
        
        // Set connection lost timeout (30 seconds)
        setConnectionLostTimeout(30);
    }

    @Override
    public void onOpen(WebSocket conn, ClientHandshake handshake) {
        String clientId = "Client-" + clientIdCounter.getAndIncrement();
        connectedClients.put(conn, clientId);
        
        plugin.getLogger().info("New WebSocket connection: " + clientId + " from " + conn.getRemoteSocketAddress());
        
        // Send welcome message
        JsonObject welcome = new JsonObject();
        welcome.addProperty("type", "welcome");
        welcome.addProperty("message", "Connected to BlockMarket World Controller");
        welcome.addProperty("clientId", clientId);
        welcome.addProperty("server", "Minecraft WebSocket Server");
        
        conn.send(welcome.toString());
        
        // Broadcast to other clients that someone joined
        broadcastToOthers(conn, "{\"type\":\"client_connected\",\"clientId\":\"" + clientId + "\"}");
    }

    @Override
    public void onClose(WebSocket conn, int code, String reason, boolean remote) {
        String clientId = connectedClients.remove(conn);
        if (clientId != null) {
            plugin.getLogger().info("WebSocket connection closed: " + clientId + " (Code: " + code + ", Reason: " + reason + ")");
            
            // Broadcast to other clients that someone left
            broadcastToOthers(conn, "{\"type\":\"client_disconnected\",\"clientId\":\"" + clientId + "\"}");
        }
    }

    @Override
    public void onMessage(WebSocket conn, String message) {
        String clientId = connectedClients.get(conn);
        plugin.getLogger().info("Message from " + clientId + ": " + message);
        
        // Process message on main thread to interact with Bukkit API
        Bukkit.getScheduler().runTask(plugin, () -> handleMessage(conn, message, clientId));
    }

    @Override
    public void onError(WebSocket conn, Exception ex) {
        String clientId = connectedClients.get(conn);
        plugin.getLogger().log(Level.SEVERE, "WebSocket error for " + clientId, ex);
        
        if (conn != null) {
            JsonObject error = new JsonObject();
            error.addProperty("type", "error");
            error.addProperty("message", "Server error occurred: " + ex.getMessage());
            conn.send(error.toString());
        }
    }


    private void handleMessage(WebSocket conn, String message, String clientId) {
        try {
            // Try to parse as JSON first
            if (message.trim().startsWith("{") && message.trim().endsWith("}")) {
                handleJsonMessage(conn, message, clientId);
            } else {
                // Handle as plain text command for backward compatibility
                handlePlainTextMessage(conn, message, clientId);
            }
        } catch (Exception e) {
            plugin.getLogger().log(Level.SEVERE, "Error handling message from " + clientId + ": " + message, e);
            sendErrorResponse(conn, "Error processing message: " + e.getMessage());
        }
    }

    private void handleJsonMessage(WebSocket conn, String jsonMessage, String clientId) {
        try {
            JsonObject json = JsonParser.parseString(jsonMessage).getAsJsonObject();
            String type = json.has("type") ? json.get("type").getAsString() : "";
            
            plugin.getLogger().info("Processing JSON message from " + clientId + " of type: " + type);
            
            switch (type.toLowerCase()) {
                case "create_trading_floor":
                    handleCreateTradingFloor(conn, json, clientId);
                    break;
                case "ping":
                    handlePing(conn, json);
                    break;
                case "broadcast":
                    handleBroadcast(conn, json, clientId);
                    break;
                case "get_server_info":
                    handleServerInfo(conn);
                    break;
                default:
                    plugin.getLogger().warning("Unknown message type from " + clientId + ": " + type);
                    sendErrorResponse(conn, "Unknown message type: " + type);
                    break;
            }
            
        } catch (JsonSyntaxException e) {
            plugin.getLogger().log(Level.WARNING, "Invalid JSON from " + clientId + ": " + jsonMessage, e);
            sendErrorResponse(conn, "Invalid JSON format");
        }
    }

    private void handleCreateTradingFloor(WebSocket conn, JsonObject json, String clientId) {
        try {
            // Parse parameters
            int size = json.has("size") ? json.get("size").getAsInt() : 10;
            String worldName = json.has("world") ? json.get("world").getAsString() : "world";
            
            // Optional center coordinates
            Integer centerX = json.has("centerX") ? json.get("centerX").getAsInt() : null;
            Integer centerZ = json.has("centerZ") ? json.get("centerZ").getAsInt() : null;
            
            // Validate size
            if (size < 3 || size > 100) {
                plugin.getLogger().warning("Invalid trading floor size from " + clientId + ": " + size);
                sendErrorResponse(conn, "Invalid size. Must be between 3 and 100.");
                return;
            }
            
            // Get world
            org.bukkit.World world = Bukkit.getWorld(worldName);
            if (world == null) {
                plugin.getLogger().warning("World not found: " + worldName + " (requested by " + clientId + ")");
                sendErrorResponse(conn, "World not found: " + worldName);
                return;
            }
            
            plugin.getLogger().info(clientId + " creating " + size + "x" + size + " trading floor in world: " + worldName);
            
            // Build the trading floor
            TradingFloorBuilder.TradingFloorResult result;
            if (centerX != null && centerZ != null) {
                result = tradingFloorBuilder.buildTradingFloorCentered(world, centerX, centerZ, size);
            } else {
                // Use world spawn as reference point
                int spawnX = world.getSpawnLocation().getBlockX();
                int spawnZ = world.getSpawnLocation().getBlockZ();
                result = tradingFloorBuilder.buildTradingFloorCentered(world, spawnX, spawnZ, size);
            }
            
            // Send success response
            JsonObject response = new JsonObject();
            response.addProperty("type", "trading_floor_created");
            response.addProperty("success", true);
            response.addProperty("centerX", result.getCenterX());
            response.addProperty("centerY", result.getCenterY());
            response.addProperty("centerZ", result.getCenterZ());
            response.addProperty("size", result.getSize());
            response.addProperty("world", worldName);
            response.addProperty("requestedBy", clientId);
            
            conn.send(response.toString());
            
            // Broadcast to other clients
            JsonObject broadcast = new JsonObject();
            broadcast.addProperty("type", "trading_floor_created_broadcast");
            broadcast.addProperty("centerX", result.getCenterX());
            broadcast.addProperty("centerY", result.getCenterY());
            broadcast.addProperty("centerZ", result.getCenterZ());
            broadcast.addProperty("size", result.getSize());
            broadcast.addProperty("world", worldName);
            broadcast.addProperty("createdBy", clientId);
            
            broadcastToOthers(conn, broadcast.toString());
            
            plugin.getLogger().info("Trading floor created by " + clientId + " at center: (" + 
                    result.getCenterX() + ", " + result.getCenterY() + ", " + result.getCenterZ() + ")");
                    
        } catch (Exception e) {
            plugin.getLogger().log(Level.SEVERE, "Error creating trading floor for " + clientId, e);
            sendErrorResponse(conn, "Failed to create trading floor: " + e.getMessage());
        }
    }

    private void handlePing(WebSocket conn, JsonObject json) {
        JsonObject pong = new JsonObject();
        pong.addProperty("type", "pong");
        pong.addProperty("timestamp", System.currentTimeMillis());
        if (json.has("timestamp")) {
            pong.addProperty("clientTimestamp", json.get("timestamp").getAsLong());
        }
        conn.send(pong.toString());
    }

    private void handleBroadcast(WebSocket conn, JsonObject json, String clientId) {
        if (json.has("message")) {
            String message = json.get("message").getAsString();
            
            JsonObject broadcast = new JsonObject();
            broadcast.addProperty("type", "broadcast_message");
            broadcast.addProperty("message", message);
            broadcast.addProperty("from", clientId);
            broadcast.addProperty("timestamp", System.currentTimeMillis());
            
            broadcastToAll(broadcast.toString());
            plugin.getLogger().info("Broadcast from " + clientId + ": " + message);
        }
    }

    private void handleServerInfo(WebSocket conn) {
        JsonObject info = new JsonObject();
        info.addProperty("type", "server_info");
        info.addProperty("serverName", Bukkit.getServer().getName());
        info.addProperty("version", Bukkit.getServer().getVersion());
        info.addProperty("onlinePlayers", Bukkit.getServer().getOnlinePlayers().size());
        info.addProperty("maxPlayers", Bukkit.getServer().getMaxPlayers());
        info.addProperty("connectedClients", connectedClients.size());
        info.addProperty("port", getPort());
        
        conn.send(info.toString());
    }

    private void handlePlainTextMessage(WebSocket conn, String message, String clientId) {
        // For backward compatibility, treat plain text as echo
        plugin.getLogger().info("Plain text message from " + clientId + ": " + message);
        
        JsonObject echo = new JsonObject();
        echo.addProperty("type", "echo");
        echo.addProperty("originalMessage", message);
        echo.addProperty("from", clientId);
        
        conn.send(echo.toString());
    }

    private void sendErrorResponse(WebSocket conn, String errorMessage) {
        JsonObject error = new JsonObject();
        error.addProperty("type", "error");
        error.addProperty("message", errorMessage);
        error.addProperty("timestamp", System.currentTimeMillis());
        
        conn.send(error.toString());
    }

    public void broadcastToAll(String message) {
        for (WebSocket client : connectedClients.keySet()) {
            if (client.isOpen()) {
                client.send(message);
            }
        }
    }

    public void broadcastToOthers(WebSocket exclude, String message) {
        for (WebSocket client : connectedClients.keySet()) {
            if (client != exclude && client.isOpen()) {
                client.send(message);
            }
        }
    }

    public int getConnectedClientCount() {
        return connectedClients.size();
    }

    private volatile boolean serverRunning = false;
    
    @Override
    public void onStart() {
        serverRunning = true;
        plugin.getLogger().info("WebSocket server started successfully on port " + getPort());
    }
    
    public boolean isServerRunning() {
        return serverRunning && getConnections() != null;
    }

    public void shutdown() {
        try {
            plugin.getLogger().info("Shutting down WebSocket server...");
            serverRunning = false;
            
            // Notify all clients about shutdown
            JsonObject shutdown = new JsonObject();
            shutdown.addProperty("type", "server_shutdown");
            shutdown.addProperty("message", "Server is shutting down");
            broadcastToAll(shutdown.toString());
            
            // Close all connections
            for (WebSocket client : connectedClients.keySet()) {
                client.close(1001, "Server shutdown");
            }
            
            // Stop the server
            stop();
            plugin.getLogger().info("WebSocket server shut down successfully");
            
        } catch (Exception e) {
            plugin.getLogger().log(Level.SEVERE, "Error during WebSocket server shutdown", e);
        }
    }
}
