package policy

import (
	"fmt"
	"policyservice/internal/storage"
)

type Evaluator struct {
	store *storage.PolicyStore
}

func NewEvaluator(store *storage.PolicyStore) *Evaluator {
	return &Evaluator{store: store}
}

func (e *Evaluator) EvaluatePriority(p ProposalFacts) PriorityResult {
	// Simply check tool tier - no directory matching
	tier := e.store.ToolRegistry.GetToolTier(p.ToolName)

	reason := fmt.Sprintf("Tool '%s' classified as %s", p.ToolName, tier)
	requiresApproval := tier == TierCritical

	// Check line threshold (optional - can keep or remove)
	totalLines := p.LinesAdded + p.LinesRemoved
	if totalLines > e.store.LineThreshold && tier == TierSafe {
		requiresApproval = true
		reason += fmt.Sprintf("; Large change (%d lines exceeds threshold of %d)", totalLines, e.store.LineThreshold)
	}

	return PriorityResult{
		Tier:             tier,
		RequiresApproval: requiresApproval,
		Reason:           reason,
		CheckpointID:     p.CheckpointID,
	}
}
