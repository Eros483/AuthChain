# AuthChain Frontend

Chat interface for the AuthChain AI agent system with human-in-the-loop approval for critical actions.

## Features

- Real-time chat interface with the AI agent
- Automatic status polling for agent execution
- Critical action approval workflow
- Message history display
- Suggestion cards for quick queries
- Responsive design with gradient background

## Setup

1. Install dependencies:
```bash
npm install
```

2. Make sure the backend is running on `http://localhost:8000`

3. Start the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000)

## How It Works

### User Flow

1. **Submit Query**: User types a question or command and sends it
2. **Agent Processing**: Frontend polls the backend for status updates every 2 seconds
3. **Critical Action Approval**: If the agent needs to perform a critical action (like deleting files), an approval card appears
4. **Final Response**: Once complete, the agent's response is displayed

### API Integration

The frontend connects to these backend endpoints:

- `POST /api/v1/agent/execute` - Start agent with query
- `GET /api/v1/agent/status/{thread_id}` - Poll execution status
- `GET /api/v1/agent/response/{thread_id}` - Get final output
- `GET /api/v1/critical-action/{thread_id}` - Get pending critical action
- `POST /api/v1/user/approve` - Submit approval/rejection

### Status Polling

The frontend polls the status endpoint to check:
- `RUNNING` - Agent is processing
- `AWAITING_APPROVAL` - Critical action needs approval
- `COMPLETED` - Task finished
- `ERROR` - Execution failed

## Components

- **ChatCanvas** - Main container with state management and polling logic
- **ChatInput** - Input field with send functionality
- **MessageBubble** - Message display component for user and AI messages
- **ApprovalCard** - Critical action approval UI with approve/reject buttons
- **SuggestionCards** - Pre-defined question suggestions

## Building for Production

```bash
npm run build
npm start
```

## Configuration

To change the API endpoint, edit `lib/api.ts`:

```typescript
const API_BASE = "http://localhost:8000/api/v1";
```
