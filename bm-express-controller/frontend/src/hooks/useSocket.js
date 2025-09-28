import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import { useAtom } from 'jotai';
import { inventoriesAtom } from '../atoms/inventory';

const useSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [socket, setSocket] = useState(null);
  const [inventories, setInventories] = useAtom(inventoriesAtom);

  useEffect(() => {
    const url = "http://localhost:3001";
    console.log("Master server URL:", url);
    
    const socketInstance = io(url, {
      transports: ["websocket"], // helps avoid long-polling issues with ngrok
    });

    setSocket(socketInstance);

    socketInstance.on("connect", () => {
      console.log("Connected to server");
      setIsConnected(true);
    });
    
    socketInstance.on("disconnect", () => {
      console.log("Disconnected from server");
      setIsConnected(false);
    });
    
    socketInstance.on("connect_error", (error) => {
      console.error("Connection error:", error);
      setIsConnected(false);
    });
    
    socketInstance.on("welcome", (msg) => {
      console.log("Welcome message: " + msg);
    });
    
    socketInstance.on("data_update", (data) => {
      console.log("Received data update:", data);
    });
    
    return () => {
      socketInstance.off("connect");
      socketInstance.off("disconnect");
      socketInstance.off("connect_error");
      socketInstance.off("welcome");
      socketInstance.off("data_update");
      socketInstance.disconnect();
    };
  }, []);

  const startSimulation = (simulationStartInventories) => {
    if (socket && isConnected) {
      // const selectedCellsArray = Array.from(selectedCells);
      socket.emit('start_simulation', { 
        botInventoryMap: Object.fromEntries(simulationStartInventories)
      });
      console.log('Starting simulation with inventories:', Object.fromEntries(simulationStartInventories));
       //console.log(`Starting simulation with ${selectedCells.size} selected cells`);
      return true;
    }
    return false;
  };

  return {
    isConnected,
    startSimulation
  };
};

export default useSocket;
