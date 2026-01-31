package policy

type ProposalFacts struct {
	ProposalID       string                 `json:"proposal_id"`
	ThreadID         string                 `json:"thread_id"`
	CheckpointID     string                 `json:"checkpoint_id"`
	ToolName         string                 `json:"tool_name"`
	ToolArguments    map[string]interface{} `json:"tool_arguments"`
	ReasoningSummary string                 `json:"reasoning_summary"`
	Timestamp        int64                  `json:"timestamp"`

	FilesChanged []string `json:"files_changed,omitempty"`
	LinesAdded   int      `json:"lines_added,omitempty"`
	LinesRemoved int      `json:"lines_removed,omitempty"`
}

type PriorityResult struct {
	Tier                string   `json:"tier"`
	RequiresApproval    bool     `json:"requires_approval"`
	AssignedDevelopers  []string `json:"assigned_developers"`
	AffectedDirectories []string `json:"affected_directories"`
	Reason              string   `json:"reason"`
	CheckpointID        string   `json:"checkpoint_id"`
}

type ApprovalDecision struct {
	ProposalID      string `json:"proposal_id"`
	CheckpointID    string `json:"checkpoint_id"`
	DecisionBy      string `json:"decision_by"`
	Approved        bool   `json:"approved"`
	RejectionReason string `json:"rejection_reason"`
	Timestamp       int64  `json:"timestamp"`
}

type BlockchainPayload struct {
	ProposalID       string                 `json:"proposal_id"`
	CheckpointID     string                 `json:"checkpoint_id"`
	ToolName         string                 `json:"tool_name"`
	ToolArguments    map[string]interface{} `json:"tool_arguments"`
	ReasoningSummary string                 `json:"reasoning_summary"`
	Decision         ApprovalDecision       `json:"decision"`
	PriorityResult   PriorityResult         `json:"priority_result"`
	Timestamp        int64                  `json:"timestamp"`
}

const (
	TierSafe     = "tier_safe"
	TierCritical = "tier_critical"
)
