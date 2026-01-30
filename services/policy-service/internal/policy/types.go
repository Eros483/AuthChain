package policy

type ProposalFacts struct {
	ProposalID   string   `json:"proposal_id"`
	ThreadID     string   `json:"thread_id"`
	ActionType   string   `json:"action_type"`
	FilesChanged []string `json:"files_changed"`
	LinesAdded   int      `json:"lines_added"`
	LinesRemoved int      `json:"lines_removed"`
}

type PriorityResult struct {
	Tier                string   `json:"priority"`
	RequiresApproval    bool     `json:"requires_approval"`
	AssignedDevelopers  []string `json:"assigned_developers"`
	AffectedDirectories []string `json:"affected_directories"`
	Reason              string   `json:"reason"`
}

type ApprovalDecision struct {
	ProposalID      string `json:"proposal_id"`
	DecisionBy      string `json:"decision_by"`
	Approved        bool   `json:"approved"`
	RejectionReason string `json:"rejection_reason"`
	Timestamp       int64  `json:"timestamp"`
}

type BlockchainPayload struct {
	ProposalID     string           `json:"proposal_id"`
	ProposalFacts  ProposalFacts    `json:"proposal_facts"`
	Decision       ApprovalDecision `json:"decision"`
	PriorityResult PriorityResult   `json:"priority_result"`
}

const (
	Tier1 = "tier1"
	Tier2 = "tier2"
)
