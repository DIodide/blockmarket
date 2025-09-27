import { useState } from 'react'
import { useEffect } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [message, setMessage] = useState([])
  const [socket, setSocket] = useState(null)
  useEffect(() => {
    
    const newSocket = new WebSocket('ws://localhost:3000')
    setSocket(newSocket)
    newSocket.onopen = () => {
        console.log("Client connected to server")
        newSocket.send("Hello from client")
    }
    newSocket.onmessage = (event) => {
        setMessage((prev) => [...prev, event.data])
    }
    newSocket.onclose = () => {
        console.log("Client disconnected from server")
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
