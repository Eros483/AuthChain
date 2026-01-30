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

	tier := e.determineTier(p.ActionType)

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

	requiresApproval := tier == Tier2

	if tier == Tier1 {
		reasons = append(reasons, "Read-only operation (Tier 1) - no approval needed")
	} else {
		reasons = append(reasons, "Write operation (Tier 2) - approval required")
	}

	totalLines := p.LinesAdded + p.LinesRemoved
	if totalLines > e.store.LineThreshold {
		reasons = append(reasons, fmt.Sprintf("Large change (%d lines exceeds threshold of %d)", totalLines, e.store.LineThreshold))
	}

	return PriorityResult{
		Tier:                tier,
		RequiresApproval:    requiresApproval,
		AssignedDevelopers:  assignedDevelopers,
		AffectedDirectories: affectedDirsNames,
		Reason:              strings.Join(reasons, "; "),
	}
}

func (e *Evaluator) determineTier(actionType string) string {
	readOnlyActions := map[string]bool{
		"read":   true,
		"view":   true,
		"get":    true,
		"fetch":  true,
		"query":  true,
		"search": true,
		"list":   true,
	}

	actionLower := strings.ToLower(actionType)

	if readOnlyActions[actionLower] {
		return Tier1
	}

	return Tier2
}
