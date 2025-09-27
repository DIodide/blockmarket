package org.blockmarket.bmWorldController;

import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitRunnable;

public class TradingFloorBuilder {
    private final JavaPlugin plugin;

    public TradingFloorBuilder(JavaPlugin plugin) {
        this.plugin = plugin;
    }

    /**
     * Builds a trading floor at the specified coordinates with a glass ceiling
     *
     * @param world The world to build in
     * @param startX Starting X coordinate
     * @param startZ Starting Z coordinate
     * @param size Size of the trading floor (n x n)
     * @return The center coordinates of the trading floor
     */
    public TradingFloorResult buildTradingFloor(World world, int startX, int startZ, int size) {
        final int floorY = 100;
        final int ceilingY = 104; // 4 blocks high

        plugin.getLogger().info("Building " + size + "x" + size + " trading floor at (" + startX + ", " + floorY + ", " + startZ + ")");

        // Run the building task asynchronously to prevent server lag
        new BukkitRunnable() {
            @Override
            public void run() {
                // Build floor
                buildFloor(world, startX, startZ, size, floorY);
                
                // Build walls
                buildWalls(world, startX, startZ, size, floorY, ceilingY);
                
                // Build glass ceiling
                buildGlassCeiling(world, startX, startZ, size, ceilingY);
                
                // Add lighting
                addLighting(world, startX, startZ, size, floorY + 1);
                
                plugin.getLogger().info("Trading floor construction completed");
            }
        }.runTask(plugin);

        // Calculate center coordinates
        int centerX = startX + (size / 2);
        int centerZ = startZ + (size / 2);
        
        return new TradingFloorResult(centerX, floorY + 1, centerZ, size);
    }

    /**
     * Builds a trading floor centered at the given location
     */
    public TradingFloorResult buildTradingFloorCentered(World world, int centerX, int centerZ, int size) {
        int startX = centerX - (size / 2);
        int startZ = centerZ - (size / 2);
        
        return buildTradingFloor(world, startX, startZ, size);
    }

    private void buildFloor(World world, int startX, int startZ, int size, int floorY) {
        // Build a polished stone floor
        for (int x = startX; x < startX + size; x++) {
            for (int z = startZ; z < startZ + size; z++) {
                Block block = world.getBlockAt(x, floorY, z);
                block.setType(Material.POLISHED_BLACKSTONE);
            }
        }
    }

    private void buildWalls(World world, int startX, int startZ, int size, int floorY, int ceilingY) {
        // Build walls with glass blocks
        for (int y = floorY + 1; y < ceilingY; y++) {
            // North and South walls
            for (int x = startX; x < startX + size; x++) {
                // North wall
                world.getBlockAt(x, y, startZ).setType(Material.GLASS);
                // South wall  
                world.getBlockAt(x, y, startZ + size - 1).setType(Material.GLASS);
            }
            
            // East and West walls
            for (int z = startZ; z < startZ + size; z++) {
                // West wall
                world.getBlockAt(startX, y, z).setType(Material.GLASS);
                // East wall
                world.getBlockAt(startX + size - 1, y, z).setType(Material.GLASS);
            }
        }
    }

    private void buildGlassCeiling(World world, int startX, int startZ, int size, int ceilingY) {
        // Build glass ceiling
        for (int x = startX; x < startX + size; x++) {
            for (int z = startZ; z < startZ + size; z++) {
                Block block = world.getBlockAt(x, ceilingY, z);
                block.setType(Material.GLASS);
            }
        }
    }

    private void addLighting(World world, int startX, int startZ, int size, int lightY) {
        // Add sea lanterns for lighting at regular intervals
        int spacing = Math.max(4, size / 6); // Ensure good lighting coverage
        
        for (int x = startX + spacing; x < startX + size - 1; x += spacing) {
            for (int z = startZ + spacing; z < startZ + size - 1; z += spacing) {
                Block block = world.getBlockAt(x, lightY + 2, z);
                block.setType(Material.SEA_LANTERN);
            }
        }
    }

    /**
     * Clears the area before building (optional, removes existing blocks)
     */
    public void clearArea(World world, int startX, int startZ, int size) {
        final int floorY = 100;
        final int clearHeight = 10;
        
        plugin.getLogger().info("Clearing area for trading floor construction");
        
        new BukkitRunnable() {
            @Override
            public void run() {
                for (int x = startX; x < startX + size; x++) {
                    for (int z = startZ; z < startZ + size; z++) {
                        for (int y = floorY; y < floorY + clearHeight; y++) {
                            Block block = world.getBlockAt(x, y, z);
                            if (!block.getType().isAir()) {
                                block.setType(Material.AIR);
                            }
                        }
                    }
                }
                plugin.getLogger().info("Area cleared successfully");
            }
        }.runTask(plugin);
    }

    /**
     * Result class containing trading floor information
     */
    public static class TradingFloorResult {
        private final int centerX;
        private final int centerY;
        private final int centerZ;
        private final int size;

        public TradingFloorResult(int centerX, int centerY, int centerZ, int size) {
            this.centerX = centerX;
            this.centerY = centerY;
            this.centerZ = centerZ;
            this.size = size;
        }

        public int getCenterX() {
            return centerX;
        }

        public int getCenterY() {
            return centerY;
        }

        public int getCenterZ() {
            return centerZ;
        }

        public int getSize() {
            return size;
        }

        public String toJson() {
            return "{\"centerX\":" + centerX + 
                   ",\"centerY\":" + centerY + 
                   ",\"centerZ\":" + centerZ + 
                   ",\"size\":" + size + "}";
        }
    }
}
