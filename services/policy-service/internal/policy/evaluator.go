package policy

import (
	"fmt"
	"policyservice/internal/storage"
	"strings"
)

type Evaluator struct {
	store *storage.PolicyStore
}

func NewEvaluator(store *storage.PolicyStore) *Evaluator {
	return &Evaluator{store: store}
}

func (e *Evaluator) EvaluatePriority(p ProposalFacts) PriorityResult {
	affectedDirs := make(map[string][]string)
	reasons := []string{}

	tier := e.store.ToolRegistry.GetToolTier(p.ToolName)

	reasons = append(reasons, fmt.Sprintf("Tool '%s' classified as %s", p.ToolName, tier))

	allOwnerships := e.store.GetAllOwnership()

	for _, file := range p.FilesChanged {
		var bestMatch *storage.DirectoryOwnership

		for i := range allOwnerships {
			ownership := &allOwnerships[i]
			if strings.HasPrefix(file, ownership.Directory) {
				if bestMatch == nil || len(ownership.Directory) > len(bestMatch.Directory) {
					bestMatch = ownership
				}
			}
		}

		if bestMatch != nil {
			if _, exists := affectedDirs[bestMatch.Directory]; !exists {
				affectedDirs[bestMatch.Directory] = bestMatch.Developers
			}
			reasons = append(reasons, fmt.Sprintf("File '%s' matches protected dir '%s'", file, bestMatch.Directory))
		}
	}

	developersMap := make(map[string]bool)
	for _, devs := range affectedDirs {
		for _, dev := range devs {
			developersMap[dev] = true
		}
	}

	assignedDevelopers := make([]string, 0, len(developersMap))
	for dev := range developersMap {
		assignedDevelopers = append(assignedDevelopers, dev)
	}

	affectedDirsNames := make([]string, 0, len(affectedDirs))
	for dir := range affectedDirs {
		affectedDirsNames = append(affectedDirsNames, dir)
	}

	requiresApproval := tier == TierCritical

	totalLines := p.LinesAdded + p.LinesRemoved
	if totalLines > e.store.LineThreshold {
		reasons = append(reasons, fmt.Sprintf("Large change (%d lines exceeds threshold of %d)", totalLines, e.store.LineThreshold))
		if tier == TierSafe {
			requiresApproval = true
			reasons = append(reasons, "Approval required due to large change size")
		}
	}

	return PriorityResult{
		Tier:                tier,
		RequiresApproval:    requiresApproval,
		AssignedDevelopers:  assignedDevelopers,
		AffectedDirectories: affectedDirsNames,
		Reason:              strings.Join(reasons, "; "),
		CheckpointID:        p.CheckpointID,
	}
}
