import { useState } from 'react'
import ChatInterface from './components/ChatInterface'
import './App.css'

function App() {
  const [darkMode, setDarkMode] = useState(false)

  return (
    <div className={`app ${darkMode ? 'dark' : 'light'}`}>
      <ChatInterface darkMode={darkMode} setDarkMode={setDarkMode} />
    </div>
  )
}

export default App
