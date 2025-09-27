package org.blockmarket.bmWorldController;

import org.bukkit.Bukkit;
import org.bukkit.plugin.java.JavaPlugin;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import java.net.URI;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;

public class WebSocketManager {
    private WebSocketClient webSocketClient;
    private final JavaPlugin plugin;
    private final String serverUrl;
    private final Consumer<String> messageHandler;
    private boolean isConnected = false;
    private int reconnectAttempts = 0;
    private final int maxReconnectAttempts = 5;
    private final long reconnectDelay = 5000; // 5 seconds

    public WebSocketManager(JavaPlugin plugin, String serverUrl, Consumer<String> messageHandler) {
        this.plugin = plugin;
        this.serverUrl = serverUrl;
        this.messageHandler = messageHandler;
    }

    public void connect() {
        try {
            URI serverUri = URI.create(serverUrl);
            webSocketClient = new WebSocketClient(serverUri) {
                @Override
                public void onOpen(ServerHandshake handshake) {
                    plugin.getLogger().info("WebSocket connected to: " + serverUrl);
                    isConnected = true;
                    reconnectAttempts = 0;
                }

                @Override
                public void onMessage(String message) {
                    plugin.getLogger().info("Received WebSocket message: " + message);
                    // Execute message handling on the main thread
                    Bukkit.getScheduler().runTask(plugin, () -> messageHandler.accept(message));
                }

                @Override
                public void onClose(int code, String reason, boolean remote) {
                    plugin.getLogger().warning("WebSocket connection closed. Code: " + code + ", Reason: " + reason);
                    isConnected = false;
                    
                    // Attempt to reconnect if not manually closed
                    if (code != 1000 && reconnectAttempts < maxReconnectAttempts) {
                        scheduleReconnect();
                    }
                }

                @Override
                public void onError(Exception ex) {
                    plugin.getLogger().severe("WebSocket error: " + ex.getMessage());
                    ex.printStackTrace();
                    isConnected = false;
                }
            };

            // Connect asynchronously
            CompletableFuture.runAsync(() -> {
                try {
                    webSocketClient.connect();
                } catch (Exception e) {
                    plugin.getLogger().severe("Failed to connect to WebSocket: " + e.getMessage());
                    scheduleReconnect();
                }
            });

        } catch (Exception e) {
            plugin.getLogger().severe("Error creating WebSocket connection: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private void scheduleReconnect() {
        if (reconnectAttempts >= maxReconnectAttempts) {
            plugin.getLogger().severe("Max reconnection attempts reached. Stopping reconnection attempts.");
            return;
        }

        reconnectAttempts++;
        plugin.getLogger().info("Scheduling reconnection attempt " + reconnectAttempts + "/" + maxReconnectAttempts + " in " + (reconnectDelay / 1000) + " seconds");
        
        Bukkit.getScheduler().runTaskLaterAsynchronously(plugin, () -> {
            if (!isConnected) {
                connect();
            }
        }, reconnectDelay / 50); // Convert milliseconds to ticks (50ms = 1 tick)
    }

    public void disconnect() {
        if (webSocketClient != null && isConnected) {
            webSocketClient.close(1000, "Plugin shutting down");
            isConnected = false;
        }
    }

    public void sendMessage(String message) {
        if (webSocketClient != null && isConnected) {
            webSocketClient.send(message);
            plugin.getLogger().info("Sent WebSocket message: " + message);
        } else {
            plugin.getLogger().warning("Cannot send message: WebSocket not connected");
        }
    }

    public boolean isConnected() {
        return isConnected;
    }

    public void forceReconnect() {
        if (webSocketClient != null) {
            webSocketClient.close();
        }
        reconnectAttempts = 0;
        connect();
    }
}
