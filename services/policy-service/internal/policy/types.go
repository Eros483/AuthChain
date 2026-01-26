package policy

type ProposalFacts struct {
	ProposalID   string   `json:"proposal_id"`
	ThreadID     string   `json:"thread_id"`
	ActionType   string   `json:"action_type"`
	FilesChanged []string `json:"files_changed"`
	LinesAdded   int      `json:"lines_added"`
	LinesRemoved int      `json:"lines_removed"`
}

type PriortiyResult struct {
	Priority     string `json:"priority"`
	RequiredRole string `json:"required_role"`
	Reason       string `json:"reason"`
}
