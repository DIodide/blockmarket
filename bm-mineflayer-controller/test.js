const mineflayer = require('mineflayer');

function printBotInventory(bot) {
  console.log('--- Bot Inventory ---');
  bot.inventory.slots.forEach((item, index) => {
    if (item) { // Check if the slot is not empty
      console.log(`Slot ${index}: ${item.name} (Count: ${item.count})`);
    }
  });
  console.log('---------------------');
}

function createBot(username) {
  const bot = mineflayer.createBot({
    host: 'mcpanel.blockwarriors.ai',  // e.g. 'localhost' or 'play.example.com'
    port: 25565,               // server port
    username,                  // bot's username
    version: '1.20.6',         // match your server version
    // auth: 'microsoft',      // uncomment if server is online-mode
  });

  bot.once('spawn', () => {
    console.log(`[${username}] spawned in!`);
    bot.chat(`Hi, I'm ${username}!`);
  });

  bot.once('spawn', () => {
    bot.chat('/give @s diamond_sword 1'); // Gives the bot a diamond sword
    bot.chat('/give @s shield 1');        // Gives the bot a shield
    // Add more commands for other items
    printBotInventory(bot);
});

  bot.on('error', (err) => console.log(`[${username}] Error:`, err));
  bot.on('kicked', (reason) => console.log(`[${username}] Kicked:`, reason));

  return bot;
}

// Create two bots
createBot('BotOne');
setTimeout(() => createBot('BotTwo'), 50); // wait 3s before second bot
