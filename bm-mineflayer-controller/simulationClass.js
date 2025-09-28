const { Sim } = require('./src/sim');

class simulationClass {
    constructor(cfg) {
        this.sim = new Sim(cfg);
        this.sim.spawnFromGrid();
    }

    // async trade_timestep(items) {
    //     arr = ['Bot1', 'Bot2', 'Bot3', 'Bot4', 'Bot5', 'Bot6', 'Bot7', 'Bot8', 'Bot9', 'Bot10',];
    //     for (let i = arr.length - 1; i > 0; i--) {
    //         const j = Math.floor(Math.random() * (i + 1));
    //         [arr[i], arr[j]] = [arr[j], arr[i]];
    //     }

    //     sim.trade(arr[0], items[0], arr[1], items[1]);
    //     sim.trade(arr[2], items[2], arr[3], items[3]);
    //     sim.trade(arr[4], items[4], arr[5], items[5]);
    //     sim.trade(arr[6], items[6], arr[7], items[7]);
    //     sim.trade(arr[8], items[8], arr[9], items[9]);

    //     await sleep(10000); 
    // }

    // Shuffle helper
    shuffle(arr) {
        for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
        }
        return arr;
    }
  
    trade_timestep(items) {
        // Generate bot names based on number of items
        const botCount = items.length; // one bot per item
        const bots = Array.from({ length: botCount }, (_, i) => `Bot${i + 1}`);
    
        // Shuffle bot order
        this.shuffle(bots);
    
        // Pair bots and items
        for (let i = 0; i < botCount; i += 2) {
        if (i + 1 >= botCount) {
            console.log("⚠️ Uneven number of items, last bot left unpaired:", bots[i]);
            break;
        }
        this.sim.trade(bots[i], items[i], bots[i + 1], items[i + 1]);
        }
    }
}
module.exports = { simulationClass };