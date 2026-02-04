package main

import (
	"log"
	"policyservice/internal/mailbox"
	"policyservice/internal/policy"
	"policyservice/internal/proposal"
	"policyservice/internal/storage"
	"time"
)

func main() {
	policyStore := storage.NewPolicyStore()
	proposalStore := proposal.NewProposalStore()
	evaluator := policy.NewEvaluator(policyStore)
	go func() {
		ticker := time.NewTicker(1 * time.Hour)
		defer ticker.Stop()
		for range ticker.C {
			removed := proposalStore.Cleanup(24 * time.Hour)
			if removed > 0 {
				log.Printf("Cleaned up %d old proposals", removed)
			}
		}
	}()
	proposalWatcher := mailbox.NewMailboxWatcher(evaluator, proposalStore)
	decisionWatcher := mailbox.NewDecisionWatcher(proposalStore)
	log.Println("Policy Service Starting")
	log.Println(" Mode: File-based IPC (Mailbox)")
	go func() {
		if err := proposalWatcher.Start(); err != nil {
			log.Fatal("Proposal watcher error:", err)
		}
	}()
	go func() {
		if err := decisionWatcher.Start(); err != nil {
			log.Fatal("Decision watcher error:", err)
		}
	}()
	select {}
}
