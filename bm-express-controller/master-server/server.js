import express from "express";
import {createServer} from "http";
import {Server} from "socket.io";

const app = express();
const server = createServer(app);
const io = new Server(server, {
    cors: {origin: "*", methods: ["GET", "POST"]}
});

const frontendNS = io.of("/frontend");
const mindFlayerNS = io.of("/mindFlayer");

frontendNS.on("connection", (socket) => {
    console.log("Frontend client connected");
    socket.emit("welcome", "Welcome to BlockMarket!");
    
    socket.on("chat message", (msg) => {
        console.log("Message: " + msg);
    })
    
    socket.on("disconnect", () => {
        console.log("Frontend client disconnected");
    })
})

mindFlayerNS.on("connection", (socket) => {
    console.log("MindFlayer client connected");
})
const port = process.env.PORT || 3001;
server.listen(port, "0.0.0.0", () => {
    console.log(`BlockMarket server running on port ${port}`);
    console.log(`Frontend namespace: /frontend`);
    console.log(`MindFlayer namespace: /mindFlayer`);
})