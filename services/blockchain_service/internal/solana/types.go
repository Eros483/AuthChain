package solana

type ExecutionLock struct {
	ProposalID string
	Approved   bool
	Rejected   bool
	Required   uint8
	Approvals  []string
}
