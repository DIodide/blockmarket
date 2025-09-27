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
    socket.on("chat message", (msg) => {
        console.log("Message: " + msg);
    })
})

mindFlayerNS.on("connection", (socket) => {
    console.log("MindFlayer client connected");
})
const port = process.env.PORT || 3001;
server.listen(port)