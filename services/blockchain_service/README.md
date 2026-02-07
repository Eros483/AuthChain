# Blockchain Service

AuthChain is using a lightweight custom built blockchain providing immutable governance logs for critical actions proposed by AI.

Instead of trusting the AI agent blindly, every sensitive operation is recorded, validated, and finalized through a blockchain-backed approval workflow.

## Why Blockchain
Blockchain is not here for just storage:

- Persist approvals and rejections immutably
- Prove who authorized an action and when
- Prevent silent or retroactive modification of AI decisions
- Provide an auditable trail suitable for production and compliance

Once a decision is finalized, it cannot be altered without breaking chain integrity.


### Saved On-Chain:
```
Proposal ID
- Tool name (example: write_file, delete_file)
- Tool arguments (path, files, etc.)
- Reasoning summary shown to the approver
- Approval or rejection decision
- Identity of approver
- Timestamp
- Validator signatures
- Hash of the previous block
```