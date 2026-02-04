import { useEffect, useRef } from 'react'
import './ChatMessages.css'

function ChatMessages({ messages, isLoading, darkMode }) {
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  return (
    <div className={`messages-container ${darkMode ? 'dark' : 'light'}`}>
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message ${message.sender}`}
        >
          <div className="message-content">
            {message.text}
          </div>
        </div>
      ))}

      {isLoading && (
        <div className="message ai">
          <div className="message-content loading">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}

export default ChatMessages
