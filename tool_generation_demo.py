# ----- Demo script for quick tool generation @ tool_generation_demo.py -----

from services.tool_creation_service.generator import generate_tool_proposal, validate_tool_code
from services.tool_creation_service.registry import tool_registry

def create_tool_interactive():
    print("=" * 80)
    print("AUTHCHAIN TOOL CREATOR DEMO")
    print("=" * 80)
    
    # Get user input
    print("\nWhat tool do you want to create?")
    
    task = input("Your tool: ").strip()
    
    if not task:
        print("No task provided. Exiting.")
        return
    
    print(f"\nCreating tool for: {task}")
    print("-" * 80)
    
    print("\n[1/4] Generating code...")
    proposal = generate_tool_proposal(task)
    print(f"Proposal tool name: {proposal.tool_name}")

    print("\n[2/4] Validating tool schema and structure...")
    validation = validate_tool_code(proposal.implementation, proposal.risk_tier)
    if validation['safe']:
        print(f"Safe")
    else:
        print(f"Failed: {validation['issues']}")
        return

    print("\n[3/4] Generated code:")
    print("-" * 80)
    print(proposal.implementation)
    print("-" * 80)
    
    print("\n[4/4] Registering...")
    tool_hash = tool_registry.register_tool(proposal, approved_by="cli_user")
    print(f"      ✓ Saved with hash: {tool_hash}")
    
    print(f"\nTool '{proposal.tool_name}' is ready to use!")
    print(f"\nSaved to: {tool_registry.registry['tools'][proposal.tool_name]['filepath']}")

    print("\n" + "=" * 80)
    print("ALL REGISTERED TOOLS")
    print("=" * 80)
    for tool in tool_registry.list_tools():
        print(f"{tool['name']} ({tool['risk_tier']})")
        print(f"{tool['description']}")
    print()

if __name__ == "__main__":
    create_tool_interactive()