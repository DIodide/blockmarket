import express from "express";
import {createServer} from "http";
import {Server} from "socket.io";

const app = express();
const server = createServer(app);
const io = new Server(server, {
    cors: {origin: "*", methods: ["GET", "POST"]}
});

const frontendNS = io.of("/frontend");
const mineFlayerNS = io.of("/mineflayer");
const modelNS = io.of("/model");

frontendNS.on("connection", (socket) => {
    console.log("Frontend client connected");
    socket.emit("welcome", "Welcome to BlockMarket!");
    
    socket.on("start_simulation", (data) => {
        console.log("Starting simulation with inventories:", data);
        mineFlayerNS.emit("start_simulation", data)
        modelNS.emit("start_simulation", data)
    })
    
    socket.on("disconnect", () => {
        console.log("Frontend client disconnected");
    })
})

mineFlayerNS.on("connection", (socket) => {
    console.log("MindFlayer client connected");
    
})

modelNS.on("connection", (socket) => {
    console.log("Model client connected");
    
    socket.on("trade", (data) => {
        console.log("hub received trade data:", data);
        mineFlayerNS.emit("trade", data);
    });
    
    socket.on("simulation_started", (data) => {
        console.log("Simulation started:", data);
    });
    
    socket.on("simulation_stopped", (data) => {
        console.log("Simulation stopped:", data);
    });
    
    socket.on("simulation_error", (data) => {
        console.log("Simulation error:", data);
    });
    
    socket.on("disconnect", () => {
        console.log("Model client disconnected");
    });
})
const port = process.env.PORT || 3001;
server.listen(port, "0.0.0.0", () => {
    console.log(`BlockMarket server running on port ${port}`);
    console.log(`Frontend namespace: /frontend`);
    console.log(`MineFlayer namespace: /mineflayer`);
})