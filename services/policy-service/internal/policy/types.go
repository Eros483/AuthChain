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
	Priority            string   `json:"priority"`
	RequiresApproval    bool     `json:"requires_approval"`
	AssignedDevelopers  []string `json:"assigned_developers"`
	AffectedDirectories []string `json:"affected_directories"`
	Reason              string   `json:"reason"`
}

const (
	PriorityHigh   = "high"
	PriorityMedium = "medium"
	PriorityLow    = "low"
)
