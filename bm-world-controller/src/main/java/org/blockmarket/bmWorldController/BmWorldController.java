package org.blockmarket.bmWorldController;

import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitRunnable;
import org.bukkit.scheduler.BukkitTask;

import java.util.logging.Level;

public final class BmWorldController extends JavaPlugin {
    
    private WebSocketManager webSocketManager;
    private CommandExecutor commandExecutor;
    private String serverUrl;
    private boolean autoReconnect;
    private BukkitTask connectionCheckTask;

    @Override
    public void onEnable() {
        // Save default configuration
        saveDefaultConfig();
        
        // Load configuration values
        loadConfiguration();
        
        // Initialize command executor
        commandExecutor = new CommandExecutor(this);
        
        // Initialize WebSocket manager
        initializeWebSocket();
        
        // Register commands
        registerCommands();
        
        getLogger().info("BlockMarket World Controller has been enabled!");
        getLogger().info("WebSocket server URL: " + serverUrl);
    }

    @Override
    public void onDisable() {
        // Cancel connection check task
        if (connectionCheckTask != null && !connectionCheckTask.isCancelled()) {
            connectionCheckTask.cancel();
            getLogger().info("Cancelled connection check task");
        }
        
        // Disconnect WebSocket
        if (webSocketManager != null) {
            webSocketManager.disconnect();
        }
        
        getLogger().info("BlockMarket World Controller has been disabled!");
    }

    private void loadConfiguration() {
        //serverUrl = getConfig().getString("websocket.server-url", "wss://unevangelical-hemiparetic-annamaria.ngrok-free.dev:8080/");
        serverUrl = "wss://unevangelical-hemiparetic-annamaria.ngrok-free.dev/";
        System.out.println("serverUrl: " + serverUrl);
        autoReconnect = getConfig().getBoolean("websocket.auto-reconnect", true);
    }

    private void initializeWebSocket() {
        try {
            webSocketManager = new WebSocketManager(this, serverUrl, this::handleWebSocketMessage);
            webSocketManager.connect();
            
            // Schedule periodic connection check
            connectionCheckTask = new BukkitRunnable() {
                @Override
                public void run() {
                    if (isEnabled() && !webSocketManager.isConnected() && autoReconnect) {
                        getLogger().warning("WebSocket disconnected, attempting to reconnect...");
                        webSocketManager.forceReconnect();
                    }
                }
            }.runTaskTimerAsynchronously(this, 20L * 30, 20L * 30); // Check every 30 seconds
            
        } catch (Exception e) {
            getLogger().log(Level.SEVERE, "Failed to initialize WebSocket connection", e);
        }
    }

    private void handleWebSocketMessage(String message) {
        if (getConfig().getBoolean("messages.log-messages", true)) {
            getLogger().info("Processing WebSocket message: " + message);
        }

        try {
            // Parse the message (you can customize this based on your WebSocket server's message format)
            String processedMessage = processMessage(message);
            
            if (processedMessage != null && !processedMessage.trim().isEmpty()) {
                // Execute the command
                boolean success = commandExecutor.executeCommand(processedMessage);
                
                if (getConfig().getBoolean("messages.log-commands", true)) {
                    if (success) {
                        getLogger().info("Command executed successfully: " + processedMessage);
                    } else {
                        getLogger().warning("Command execution failed: " + processedMessage);
                    }
                }
            }
            
        } catch (Exception e) {
            getLogger().log(Level.SEVERE, "Error processing WebSocket message: " + message, e);
        }
    }

    private String processMessage(String message) {
        // Basic message processing - you can customize this based on your needs
        String processed = message.trim();
        
        // Remove color codes if configured
        if (getConfig().getBoolean("security.strip-color-codes", true)) {
            processed = processed.replaceAll("&[0-9a-fk-or]", "");
        }
        
        // Check command length
        int maxLength = getConfig().getInt("security.max-command-length", 256);
        if (maxLength > 0 && processed.length() > maxLength) {
            getLogger().warning("Command too long, truncating: " + processed.length() + " > " + maxLength);
            processed = processed.substring(0, maxLength);
        }
        
        // Validate command syntax if configured
        if (getConfig().getBoolean("security.validate-commands", true)) {
            if (!isValidCommand(processed)) {
                getLogger().warning("Invalid command syntax: " + processed);
                return null;
            }
        }
        
        return processed;
    }

    private boolean isValidCommand(String command) {
        // Basic command validation
        if (command == null || command.trim().isEmpty()) {
            return false;
        }
        
        // Check for basic command structure
        String[] parts = command.split(" ");
        if (parts.length == 0) {
            return false;
        }
        
        // Check for dangerous patterns
        String lowerCommand = command.toLowerCase();
        if (lowerCommand.contains("&&") || lowerCommand.contains("||") || lowerCommand.contains(";")) {
            return false;
        }
        
        return true;
    }

    private void registerCommands() {
        // Register any plugin commands here if needed
        // For example: getCommand("bmcontroller").setExecutor(new BmControllerCommand(this));
    }

    // Public methods for other classes to use
    public WebSocketManager getWebSocketManager() {
        return webSocketManager;
    }

    public CommandExecutor getCommandExecutor() {
        return commandExecutor;
    }

    public void sendWebSocketMessage(String message) {
        if (webSocketManager != null && webSocketManager.isConnected()) {
            webSocketManager.sendMessage(message);
        } else {
            getLogger().warning("Cannot send WebSocket message: Not connected");
        }
    }

    public boolean isWebSocketConnected() {
        return webSocketManager != null && webSocketManager.isConnected();
    }
}
