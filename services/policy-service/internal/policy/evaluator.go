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
	totalLines := p.LinesAdded + p.LinesRemoved
	affectedDirs := make(map[string][]string)
	highestPriority := ""
	reasons := []string{}

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

			if highestPriority == "" || comparePriority(bestMatch.Priority, highestPriority) > 0 {
				highestPriority = bestMatch.Priority
			}

			reasons = append(reasons, fmt.Sprintf("File '%s' matches protected Dir '%s'", file, bestMatch.Directory))
		}
	}

	exceedsThreshold := totalLines > e.store.LineThreshold
	if exceedsThreshold {
		reasons = append(reasons, fmt.Sprintf("Change size (%d lines) exceeds threshold (%d)", totalLines, e.store.LineThreshold))

		if highestPriority == "" {
			highestPriority = e.store.DefaultPriority
		}
	}

	if highestPriority == "" {
		highestPriority = PriorityLow
		reasons = append(reasons, "No Protected Dir effected withing the line threshold")
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

	reqApproval := highestPriority == PriorityHigh || exceedsThreshold

	return PriorityResult{
		Priority:            highestPriority,
		RequiresApproval:    reqApproval,
		AssignedDevelopers:  assignedDevelopers,
		AffectedDirectories: affectedDirsNames,
		Reason:              strings.Join(reasons, "; "),
	}
}

func comparePriority(p1, p2 string) int {
	PrioritMap := map[string]int{
		PriorityHigh:   3,
		PriorityMedium: 2,
		PriorityLow:    1,
	}

	val1, ok1 := PrioritMap[p1]
	val2, ok2 := PrioritMap[p2]

	if !ok1 || !ok2 {
		return 0
	}

	if val1 > val2 {
		return 1
	} else if val1 < val2 {
		return -1
	}
	return 0
}
