import { useState } from 'react'
import { useEffect } from 'react'
import {io} from 'socket.io-client'
import './App.css'
const socket = io("https://geographical-clonic-jimena.ngrok-free.dev/frontend", {
    transports: ["websocket"], // helps avoid long-polling issues with ngrok
  });
function App() {
  const [count, setCount] = useState(0)

  useEffect(() => {
    socket.on("connect", () => {
      console.log("Connected to server")
    
    })
    
    socket.on("disconnect", () => {
      console.log("Disconnected from server")
   
    })
    
    socket.on("connect_error", (error) => {
      console.error("Connection error:", error)
     
    })
    
    socket.on("welcome", (msg) => {
      console.log("Welcome message: " + msg)
    
    })
    
    return () => {
      socket.off("connect")
      socket.off("disconnect")
      socket.off("connect_error")
      socket.off("welcome")
    }
  }, [])
  
  
  return (
    <div className="App">
      <header className="App-header">
        <h1>BlockMarket</h1>
        <p>Welcome to BlockMarket - Your decentralized marketplace</p>
        
       
        
        
        
        <div className="card">
          <button onClick={() => setCount((count) => count + 1)}>
            count is {count}
          </button>
          <p>
            Edit <code>src/App.jsx</code> and save to test HMR
          </p>
        </div>
        <p className="read-the-docs">
          Click on the Vite and React logos to learn more
        </p>
      </header>
    </div>
  )
}

export default App
