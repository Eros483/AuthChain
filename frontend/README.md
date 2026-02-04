# AuthChain Frontend

Interactive chatbot UI built with React and Vite.

## Features

- Clean, modern chat interface matching the provided design
- Dark mode support with smooth transitions
- Gradient backgrounds (light: white to pink/purple, dark: dark blue tones)
- Interactive suggestion cards for quick queries
- Real-time message display with typing indicators
- Smooth animations and transitions
- Fully responsive design
- Glass morphism effects on cards and inputs

## Getting Started

Install dependencies:
```bash
npm install
```

Run development server:
```bash
npm run dev
```

Build for production:
```bash
npm run build
```

## Project Structure

- `src/App.jsx` - Main app component with theme state
- `src/components/ChatInterface.jsx` - Main chat container
- `src/components/Header.jsx` - Top header with theme toggle
- `src/components/EmptyState.jsx` - Initial view with suggestions
- `src/components/ChatMessages.jsx` - Message list display
- `src/components/InputArea.jsx` - Message input field

## Theme Toggle

Click the sun/moon icon in the top-right to switch between light and dark modes.

## Next Steps

- Connect to backend AI service for real responses
- Add chat history persistence with Supabase
- Implement approval/rejection UI for critical tool calls
- Add user authentication