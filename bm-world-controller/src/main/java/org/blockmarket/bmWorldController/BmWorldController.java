package org.blockmarket.bmWorldController;

import org.bukkit.Bukkit;
import org.bukkit.World;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitRunnable;
import org.bukkit.scheduler.BukkitTask;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonSyntaxException;

import java.util.logging.Level;

public final class BmWorldController extends JavaPlugin {
    
    private WebSocketServer webSocketServer;
    private CommandExecutor commandExecutor;
    private TradingFloorBuilder tradingFloorBuilder;
    private int webSocketPort;
    private boolean webSocketEnabled;

    @Override
    public void onEnable() {
        // Save default configuration
        saveDefaultConfig();
        
        // Load configuration values
        loadConfiguration();
        
        // Initialize command executor
        commandExecutor = new CommandExecutor(this);
        
        // Initialize trading floor builder
        tradingFloorBuilder = new TradingFloorBuilder(this);
        
        // Initialize WebSocket server
        initializeWebSocketServer();
        
        // Register commands
        registerCommands();
        
        getLogger().info("BlockMarket World Controller has been enabled!");
        if (webSocketEnabled) {
            getLogger().info("WebSocket server will start on port: " + webSocketPort);
        }
    }

    @Override
    public void onDisable() {
        // Shutdown WebSocket server
        if (webSocketServer != null) {
            webSocketServer.shutdown();
        }
        
        getLogger().info("BlockMarket World Controller has been disabled!");
    }

    private void loadConfiguration() {
        webSocketEnabled = getConfig().getBoolean("websocket.enabled", true);
        webSocketPort = getConfig().getInt("websocket.port", 8080);
        getLogger().info("WebSocket server configured - Enabled: " + webSocketEnabled + ", Port: " + webSocketPort);
    }

    private void initializeWebSocketServer() {
        if (!webSocketEnabled) {
            getLogger().info("WebSocket server is disabled in configuration");
            return;
        }
        
        try {
            webSocketServer = new WebSocketServer(this, webSocketPort, tradingFloorBuilder);
            webSocketServer.start();
            
            getLogger().info("WebSocket server starting on port " + webSocketPort);
            getLogger().info("Clients can connect to: ws://your-server-ip:" + webSocketPort);
            
        } catch (Exception e) {
            getLogger().log(Level.SEVERE, "Failed to start WebSocket server on port " + webSocketPort, e);
        }
    }


    private void registerCommands() {
        // Register any plugin commands here if needed
        // For example: getCommand("bmcontroller").setExecutor(new BmControllerCommand(this));
    }

    // Public methods for other classes to use
    public WebSocketServer getWebSocketServer() {
        return webSocketServer;
    }

    public CommandExecutor getCommandExecutor() {
        return commandExecutor;
    }

    public TradingFloorBuilder getTradingFloorBuilder() {
        return tradingFloorBuilder;
    }

    public void broadcastWebSocketMessage(String message) {
        if (webSocketServer != null) {
            webSocketServer.broadcastToAll(message);
            getLogger().info("Broadcasting message to " + webSocketServer.getConnectedClientCount() + " clients");
        } else {
            getLogger().warning("Cannot broadcast WebSocket message: Server not running");
        }
    }

    public boolean isWebSocketServerRunning() {
        return webSocketServer != null && webSocketServer.isServerRunning();
    }

    public int getConnectedClientCount() {
        return webSocketServer != null ? webSocketServer.getConnectedClientCount() : 0;
    }
}



