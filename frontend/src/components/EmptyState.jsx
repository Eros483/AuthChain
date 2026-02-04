import './EmptyState.css'

function EmptyState({ suggestions, onSuggestionClick, darkMode }) {
  return (
    <div className={`empty-state ${darkMode ? 'dark' : 'light'}`}>
      <div className="sparkle-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L13.5 8.5L20 10L13.5 11.5L12 18L10.5 11.5L4 10L10.5 8.5L12 2Z"
                fill="currentColor"
                stroke="currentColor"
                strokeWidth="0.5"/>
          <path d="M19 3L19.5 5.5L22 6L19.5 6.5L19 9L18.5 6.5L16 6L18.5 5.5L19 3Z"
                fill="currentColor"
                stroke="currentColor"
                strokeWidth="0.5"/>
        </svg>
      </div>

      <h2 className="main-heading">Ask our AI anything</h2>

      <div className="suggestions-section">
        <p className="suggestions-label">Suggestions on what to ask Our AI</p>

        <div className="suggestions-grid">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              className="suggestion-card"
              onClick={() => onSuggestionClick(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default EmptyState
