import { useState } from 'react'
import Header from './Header'
import EmptyState from './EmptyState'
import ChatMessages from './ChatMessages'
import InputArea from './InputArea'
import './ChatInterface.css'

function ChatInterface({ darkMode, setDarkMode }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const suggestions = [
    "What can I ask you to do?",
    "Which one of my projects is performing the best?",
    "What projects should I be concerned about right now?"
  ]

  const handleSuggestionClick = (suggestion) => {
    handleSendMessage(suggestion)
  }

  const handleSendMessage = async (messageText) => {
    const textToSend = messageText || input.trim()

    if (!textToSend) return

    const userMessage = {
      id: Date.now(),
      text: textToSend,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    setTimeout(() => {
      const aiMessage = {
        id: Date.now() + 1,
        text: `I received your message: "${textToSend}". This is a demo response. Connect me to your backend to get real AI responses!`,
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])
      setIsLoading(false)
    }, 1000)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className={`chat-interface ${darkMode ? 'dark' : 'light'}`}>
      <Header darkMode={darkMode} setDarkMode={setDarkMode} />

      <div className="chat-content">
        {messages.length === 0 ? (
          <EmptyState
            suggestions={suggestions}
            onSuggestionClick={handleSuggestionClick}
            darkMode={darkMode}
          />
        ) : (
          <ChatMessages messages={messages} isLoading={isLoading} darkMode={darkMode} />
        )}
      </div>

      <InputArea
        input={input}
        setInput={setInput}
        onSend={handleSendMessage}
        onKeyPress={handleKeyPress}
        darkMode={darkMode}
      />
    </div>
  )
}

export default ChatInterface
