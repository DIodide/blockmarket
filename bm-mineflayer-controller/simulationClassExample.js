// example.js
const { simulationClass } = require('./simulationClass');

// 3x3 grid; 1 = spawn a bot at that cell (row-major)
const grid = []
for (let i = 0; i < 10; i++) {
  const row = []
  for (let j = 0; j < 10; j++) {
    row.push(0)
  }
  grid.push(row)
}

grid[9][0] = 1
grid[9][9] = 1
grid[0][0] = 1
grid[0][9] = 1
grid[5][4] = 1
grid[5][5] = 1
grid[2][2] = 1
grid[8][8] = 1
grid[2][8] = 1
grid[8][2] = 1
// grid[0][0] = 1
// grid[0][1] = 1
// grid[0][2] = 1
// grid[0][3] = 1
// grid[0][4] = 1
// grid[0][5] = 1
// grid[0][6] = 1
// grid[0][7] = 1
// grid[0][8] = 1
// grid[0][9] = 1

const sim = new simulationClass({
  host: 'mcpanel.blockwarriors.ai',   // NOT the panel domain
  port: 25565,
  version: '1.20.6',
  auth: 'offline',                  // use 'microsoft' on online-mode servers
  usernames: Array.from({length: 10}, (_, i) => `Bot${i+1}`),
  grid,
  base: { x: -13.5, y: -60, z: -13.5 },      // origin of grid
  spacing: 27/9                        // blocks between grid cells
});

// everything here should happen after bots are spawned
setTimeout(() => {
    for (let phase = 0; phase < 4; phase++) {

        items = ['apple', 'gold_ingot', 'apple', 'gold_ingot', 'apple', 'gold_ingot', 'apple', 'gold_ingot', 'apple', 'gold_ingot'];
        
        setTimeout(() => {
          sim.trade_timestep(items);
        }, 0 + phase * 9500);
      }
    
}, 5000);


console.log('Trade animation complete.');