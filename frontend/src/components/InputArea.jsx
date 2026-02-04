import './InputArea.css'

function InputArea({ input, setInput, onSend, onKeyPress, darkMode }) {
  return (
    <div className={`input-area ${darkMode ? 'dark' : 'light'}`}>
      <div className="input-container">
        <input
          type="text"
          className="message-input"
          placeholder="Ask me anything about your projects"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={onKeyPress}
        />

        <button
          className="send-button"
          onClick={() => onSend()}
          disabled={!input.trim()}
          aria-label="Send message"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    </div>
  )
}

export default InputArea
