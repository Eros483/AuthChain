# Blockchain Service

AuthChain is using a lightweight custom built blockchain providing immutable governance logs for critical actions proposed by AI.

Instead of trusting the AI agent blindly, every sensitive operation is recorded, validated, and finalized through a blockchain-backed approval workflow.

## Why Blockchain
Blockchain is not here for just storage:

- Persist approvals and rejections immutably.
- Prove who authorized an action and when.
- Prevent silent or retroactive modification of AI decisions.
- Provide an auditable trail suitable for production and compliance.

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

## Governance Model
AuthChain is using a role-based criticality model:

- Safe actions are executed without pause
- Critical tools are predefined in system
- When a critical tool detected execution is paused
- User approval is required to proceed

## Directory Based Ownership

For file-system modifying actions, AuthChain supports directory ownership rules.

Example:
```
- Changes to src/auth may require approval from specific owners
- Owners are mapped to directory prefixes
- Required validators are derived automatically from the affected paths
```
This allows teams to enforce real-world responsibility boundaries in AI execution.

## Consensus
AuthChain uses a validator-based quorum model:

```
- A block is proposed after approval
- Active validators sign the block
- The block is finalized only when quorum is reached
- The finalized chain state is persisted to disk
```
Until quorum is achieved, the block remains pending and is not committed.

## Blockchain Persistence

Blockchain state is stored locally as data/blockchain.json The file is written only after finalization

Restarting the service reloads the chain safely

# API
| Endpoint                       | Description                           |
| ------------------------------ | ------------------------------------- |
| `POST /api/actions`            | Submit a proposed critical action     |
| `POST /api/blocks`             | Record approval or rejection decision |
| `GET /api/blocks`              | Retrieve full blockchain              |
| `GET /api/blocks/:index`       | Retrieve a specific block             |
| `GET /api/blocks/proposal/:id` | Retrieve blocks for a proposal        |
| `POST /api/verify`             | Verify blockchain integrity           |
| `POST /api/validators`         | Register a validator                  |
| `GET /api/validators`          | List active validators                |
| `DELETE /api/validators/:id`   | Deactivate a validator                |
| `GET /api/health`              | Blockchain service health             |

### Security Guarantees

AuthChain provides:

- Tamper-evident execution history
- Explicit human approval for critical actions
- Immutable audit trail
- Deterministic governance rules
- Clear separation between AI reasoning and execution authority

### Design Philosophy

The blockchain layer is intentionally minimal.

It exists to:
- Enforce governance
- Preserve trust
- Make AI safe enough for real execution environments
- Not to add unnecessary complexity