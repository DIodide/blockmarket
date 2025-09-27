import { useState } from 'react'
import { useEffect } from 'react'
import {io} from 'socket.io-client'
import './App.css'
const socket = io('http://localhost:3001/frontend')
function App() {
  const [count, setCount] = useState(0)
    useEffect(() => {
    socket.on("connect", () => {
      console.log("Connected to server")
    })
    socket.on("welcome", (msg) => {
      console.log("Welcome message: " + msg)
         })
    return () => {
        socket.off("connect")
        socket.off("welcome")
      }
   
  })
  
  
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
