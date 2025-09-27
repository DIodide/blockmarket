package org.blockmarket.bmWorldController;

import org.bukkit.Bukkit;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.Arrays;
import java.util.List;
import java.util.logging.Level;

public class CommandExecutor {
    private final JavaPlugin plugin;
    private final List<String> allowedCommands;
    private final List<String> blockedCommands;

    public CommandExecutor(JavaPlugin plugin) {
        this.plugin = plugin;
        this.allowedCommands = plugin.getConfig().getStringList("allowed-commands");
        this.blockedCommands = plugin.getConfig().getStringList("blocked-commands");
    }

    public boolean executeCommand(String command) {
        if (command == null || command.trim().isEmpty()) {
            plugin.getLogger().warning("Received empty command");
            return false;
        }

        // Remove leading slash if present
        String cleanCommand = command.startsWith("/") ? command.substring(1) : command;
        
        // Split command and arguments
        String[] parts = cleanCommand.split(" ");
        String commandName = parts[0].toLowerCase();

        // Check if command is blocked
        if (isCommandBlocked(commandName)) {
            plugin.getLogger().warning("Command blocked: " + commandName);
            return false;
        }

        // Check if command is allowed (if whitelist is enabled)
        if (!allowedCommands.isEmpty() && !isCommandAllowed(commandName)) {
            plugin.getLogger().warning("Command not in allowed list: " + commandName);
            return false;
        }

        // Check for dangerous commands
        if (isDangerousCommand(commandName)) {
            plugin.getLogger().warning("Dangerous command blocked: " + commandName);
            return false;
        }

        // Execute the command
        try {
            plugin.getLogger().info("Executing command: " + cleanCommand);
            
            // Use the console command sender for maximum compatibility
            CommandSender sender = Bukkit.getConsoleSender();
            
            // Execute the command
            boolean success = Bukkit.dispatchCommand(sender, cleanCommand);
            
            if (success) {
                plugin.getLogger().info("Command executed successfully: " + cleanCommand);
            } else {
                plugin.getLogger().warning("Command execution failed: " + cleanCommand);
            }
            
            return success;
            
        } catch (Exception e) {
            plugin.getLogger().log(Level.SEVERE, "Error executing command: " + cleanCommand, e);
            return false;
        }
    }

    private boolean isCommandBlocked(String commandName) {
        return blockedCommands.contains(commandName.toLowerCase());
    }

    private boolean isCommandAllowed(String commandName) {
        return allowedCommands.contains(commandName.toLowerCase());
    }

    private boolean isDangerousCommand(String commandName) {
        List<String> dangerousCommands = Arrays.asList(
            "stop", "restart", "reload", "reload-all", "save-all", "save-off", "save-on",
            "whitelist", "ban", "ban-ip", "pardon", "pardon-ip", "kick", "op", "deop",
            "setworldspawn", "setworldspawn", "world", "worlds", "multiverse", "mv"
        );
        
        return dangerousCommands.contains(commandName.toLowerCase());
    }

    public void sendMessageToPlayer(String playerName, String message) {
        Player player = Bukkit.getPlayer(playerName);
        if (player != null && player.isOnline()) {
            player.sendMessage(message);
            plugin.getLogger().info("Message sent to player " + playerName + ": " + message);
        } else {
            plugin.getLogger().warning("Player not found or offline: " + playerName);
        }
    }

    public void broadcastMessage(String message) {
        Bukkit.getServer().broadcastMessage(message);
        plugin.getLogger().info("Broadcast message: " + message);
    }

    public void sendTitleToPlayer(String playerName, String title, String subtitle, int fadeIn, int stay, int fadeOut) {
        Player player = Bukkit.getPlayer(playerName);
        if (player != null && player.isOnline()) {
            player.sendTitle(title, subtitle, fadeIn, stay, fadeOut);
            plugin.getLogger().info("Title sent to player " + playerName + ": " + title);
        } else {
            plugin.getLogger().warning("Player not found or offline: " + playerName);
        }
    }
}
