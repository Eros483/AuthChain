import os
import uuid
from services.ai_service.agent.graph import graph
from services.ai_service.ipc.messenger import send_to_blockchain
from langchain_core.messages import AIMessage, ToolMessage

def run_coding_agent(user_query: str):
    os.makedirs("./services/ipc_mailbox/ai", exist_ok=True)
    os.makedirs("./services/ipc_mailbox/blockchain", exist_ok=True)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [{"role": "user", "content": user_query}]}
    
    print(f"\n{'='*60}\n🚀 AGENT SESSION STARTING\nID: {thread_id}\n{'='*60}")

    for event in graph.stream(inputs, config, stream_mode="updates"):
        for node_name, data in event.items():
            print(f"\n[NODE: {node_name}]")
            
            if "messages" in data:
                last_msg = data["messages"][-1]

                if isinstance(last_msg, AIMessage):
                    if last_msg.tool_calls:
                        for tc in last_msg.tool_calls:
                            print(f"PLANNING TOOL: {tc['name']}")
                            print(f"ARGS: {tc['args']}")
                    if last_msg.content:
                        print(f"🤖 AI THOUGHT: {last_msg.content}")
                
                elif isinstance(last_msg, ToolMessage):
                    print(f"TOOL RESULT: {last_msg.content}")

    state = graph.get_state(config)
    if state.next:
        payload = send_to_blockchain(state.values, thread_id)
        
        print("\n" + "!"*20 + " GOVERNANCE REQUIRED " + "!"*20)
        print(f"CRITICAL TOOL DETECTED: {payload['tool_name']}")
        print(f"REASONING SUMMARY: {payload['reasoning_summary']}")
        print("!"*60)

        choice = input("\n[SIMULATED BC] Approve Proposal? (y/n): ")
        
        if choice.lower() == 'y':
            print("\nAPPROVAL RECEIVED. RESUMING...")
            for event in graph.stream(None, config, stream_mode="updates"):
                print(f"[NODE: {list(event.keys())[0]}] ...executing approved tool.")
            print("\nTASK COMPLETED.")
        else:
            print("\nREJECTION RECEIVED. INJECTING POLICY FEEDBACK...")
            rejection = "REJECTED: Security Policy violation. Direct database deletion is strictly prohibited."
            graph.update_state(config, {"messages": [{"role": "user", "content": rejection}]}, as_node="agent")
            
            for event in graph.stream(None, config, stream_mode="updates"):
                node = list(event.keys())[0]
                if node == "agent":
                    msg = event[node]["messages"][-1]
                    print(f"\n[NODE: agent]\n🤖 RECOVERY RESPONSE: {msg.content}")

if __name__ == "__main__":
    query = (
        "Scan the database projects. If any are deprecated, list the files in the sandbox, "
        "then delete the task_tracker.db and update app.py to say 'Cleaned'."
    )
    run_coding_agent(query)