from agent.graph import graph
from ipc.messenger import create_ipc_payload
import uuid

def run_demo():
    """
    Prototype AI critical tool execution workflow.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    inputs = {"messages": [{"role": "user", "content": "The database is cluttered. Delete data.db to start fresh."}]}
    
    print("--- STARTING AGENT ---")
    for event in graph.stream(inputs, config, stream_mode="values"):
        pass

    state = graph.get_state(config)
    if state.next:
        print("\n🛑 CRITICAL ACTION DETECTED!")
        payload = create_ipc_payload(state.values, thread_id)
        print(f"IPC Payload for Blockchain:\n{payload}")

        user_input = input("\nApprove this action? (y/n): ")
        
        if user_input.lower() == 'y':
            print("--- RESUMING EXECUTION ---")
            for event in graph.stream(None, config, stream_mode="values"):
                pass
        else:
            print("--- ACTION REJECTED BY USER ---")
            rejection_msg = "User rejected this: Deleting the database is not allowed under security policy."
            graph.update_state(config, {"messages": [{"role": "user", "content": rejection_msg}]}, as_node="critical_gate")
            
            for event in graph.stream(None, config, stream_mode="values"):
                if "messages" in event:
                    print(f"\nAgent's Response to Rejection: {event['messages'][-1].content}")

if __name__ == "__main__":
    run_demo()