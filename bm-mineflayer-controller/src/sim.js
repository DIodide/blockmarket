// src/sim.js
const mineflayer = require('mineflayer');
const { pathfinder, Movements, goals: { GoalBlock,GoalNear } } = require('mineflayer-pathfinder');
const mcDataFor = require('minecraft-data');
const { Vec3 } = require('vec3');

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

class Sim {
  /**
   * @param {{
   *  host: string,
   *  port: number,
   *  version?: string,         // e.g. '1.20.6'
   *  auth?: 'microsoft'|'offline',
   *  usernames: string[],      // supply as many as you’ll need
   *  grid: (0|1)[][],          // 2D matrix; 1 = place a bot at that cell
   *  base: { x: number, y: number, z: number },  // world origin of grid
   *  spacing?: number          // block spacing between cells
   * }} cfg
   */
  constructor(cfg) {
    this.cfg = { spacing: 4, auth: 'offline', ...cfg };
    this.bots = [];          // array of mineflayer bot instances
    this.byName = new Map(); // name -> bot
  }

  /** create + init one bot, then move to its “home” */
  async createBot(username, homePos) {
    const bot = mineflayer.createBot({
      host: this.cfg.host,
      port: this.cfg.port,
      version: this.cfg.version,
      auth: this.cfg.auth,
      username
    });

    bot.meta = { home: homePos }

    bot.loadPlugin(pathfinder);
  
    bot.once('spawn', () => {
      const mcData = mcDataFor(bot.version);
      const mov = new Movements(bot, mcData);
      bot.pathfinder.setMovements(mov);
      console.log(`${username} spawned!`)
      bot.chat(`${username} spawned!`)

      // update map
      this.byName.set(username, bot);

      // make bot goto their home square
      const goal = new GoalBlock(bot.meta.home.x, bot.meta.home.y, bot.meta.home.z)
      bot.pathfinder.setGoal(goal)

    })

    await sleep(3000);
  
    bot.on('error', err => console.log(`${username} error:`, err))
    bot.on('kicked', reason => console.log(`${username} kicked:`, reason))
  }

  /**
   * Spawns bots following the 2D grid.
   * The i-th true cell uses usernames[i] (in row-major order).
   */
  spawnFromGrid() {
    const { grid, usernames, base, spacing } = this.cfg;
    let nameIdx = 0;
    const tasks = [];

    for (let row = 0; row < grid.length; row++) {
      for (let col = 0; col < grid[row].length; col++) {
        if (!grid[row][col]) continue;
        if (nameIdx >= usernames.length) throw new Error('Not enough usernames provided for grid.');

        // Compute target “home” on the plane at base.y
        const x = base.x + col * spacing;
        const z = base.z + row * spacing;
        const y = base.y;

        const username = usernames[nameIdx++];
        const home = new Vec3(x, y, z);

        let bot = this.createBot(username, home);
        this.bots.push(bot);
        this.byName.set(username, bot);
      }
    }
    console.log(`[sim] Spawned ${this.bots.length} bot(s) onto the grid.`);
  }

  /**
   * Creative mode trade animation: Clear inventories, give each bot their item, 
   * have them meet in center, jump, and celebrate with particle effects
   * @param {string} bot1Name - Name of first bot
   * @param {string} item1 - Item for first bot to hold (e.g. 'diamond_sword')
   * @param {string} bot2Name - Name of second bot  
   * @param {string} item2 - Item for second bot to hold (e.g. 'emerald')
   */
  async trade(bot1Name, item1, bot2Name, item2) {
    const bot1 = this.byName.get(bot1Name);
    const bot2 = this.byName.get(bot2Name);

    // face each other
    this.faceBot(bot1, bot2);
    this.faceBot(bot2, bot1);
    await sleep(200);

    // clear inventories
    bot1.chat(`/clear`);
    bot2.chat(`/clear`);

    await sleep(200);

    // get items
    bot1.chat(`/give @s ${item1} 1`);
    bot2.chat(`/give @s ${item2} 1`);

    await sleep(200);

    // equip items
    bot1.setQuickBarSlot(0)
    bot2.setQuickBarSlot(0)

    await sleep(200);

    // meet in the center
    let center = new Vec3( (bot1.meta.home.x + bot2.meta.home.x) / 2, 
      bot1.meta.home.y, 
      (bot1.meta.home.z + bot2.meta.home.z) / 2
    )
    bot1.pathfinder.setGoal(new GoalNear(center.x, center.y, center.z, 1.2))
    bot2.pathfinder.setGoal(new GoalNear(center.x, center.y, center.z, 1.2))

    await sleep(3000);

    // throw items
    bot1.tossStack(bot1.heldItem);
    bot2.tossStack(bot2.heldItem);
    await sleep(500);

    // celebrate
    bot1.chat(`/particle happy_villager ~ ~1 ~ 0.5 0.5 0.5 0 30 force`);
    bot2.chat(`/particle happy_villager ~ ~1 ~ 0.5 0.5 0.5 0 30 force`);
    // bot1.chat(`/particle end_rod ~ ~2 ~ 0.7 1.0 0.7 0 50 normal`);
    // bot2.chat(`/particle end_rod ~ ~2 ~ 0.7 1.0 0.7 0 50 normal`);
    // bot1.chat(`/particle totem_of_undying ~ ~2 ~ 1 1 1 0 40 force`);
    // bot2.chat(`/particle totem_of_undying ~ ~2 ~ 1 1 1 0 40 force`);
    bot1.chat(`/particle firework ~ ~3 ~ 1.5 1.5 1.5 0 60 force`);
    bot2.chat(`/particle firework ~ ~3 ~ 1.5 1.5 1.5 0 60 force`);
    // bot1.chat(`/particle happy_villager ~ ~1 ~ 0.5 0.5 0.5 0 30 force`);
    // bot2.chat(`/particle happy_villager ~ ~1 ~ 0.5 0.5 0.5 0 30 force`);
    await sleep(500);

    // kill ground items 
    bot1.chat(`/kill @e[type=minecraft:item]`);
    await sleep(500);

    // equip opposite items
    bot1.chat(`/give @s ${item2} 1`);
    bot2.chat(`/give @s ${item1} 1`);
    await sleep(500);
    bot1.setQuickBarSlot(0)
    bot2.setQuickBarSlot(0)
    await sleep(500);

    // jump
    bot1.setControlState('jump', true);
    bot2.setControlState('jump', true);
    await sleep(500);
    bot1.setControlState('jump', false);
    bot2.setControlState('jump', false);
    await sleep(500);

    // go back to home
    bot1.pathfinder.setGoal(new GoalBlock(bot1.meta.home.x, bot1.meta.home.y, bot1.meta.home.z))
    bot2.pathfinder.setGoal(new GoalBlock(bot2.meta.home.x, bot2.meta.home.y, bot2.meta.home.z))

    await sleep(3000);

    // bot1.chat(`/clear`);
    // bot2.chat(`/clear`);


    await sleep(200);
  }

  get_bot_by_name(name) {
    return this.byName.get(name);
  }


    // Helper: aim botA at botB's eyes (uses a callback that resolves when rotation finishes)
  faceBot(botA, botB, force = true) {
    // Player eye height is ~1.62 blocks
    const target = botB.entity?.position
      ? botB.entity.position.offset(0, 1.62, 0)
      : new Vec3(botB.meta.home.x, botB.meta.home.y + 1.62, botB.meta.home.z)

    botA.lookAt(target, force)
    
  }
}



module.exports = { Sim };

