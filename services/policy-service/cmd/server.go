// policy-service/cmd/server.go
package main

import (
	"log"
	"time"

	"policyservice/internal/api"
	"policyservice/internal/policy"
	"policyservice/internal/proposal"
	"policyservice/internal/storage"
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

	handler := api.NewHandler(evaluator, proposalStore)
	router := api.SetupRouter(handler)

	log.Println("Policy Service Starting")
	log.Println("   Port: 8080")
	log.Println("   Endpoints:")
	log.Println("      POST   /api/evaluate")
	log.Println("      POST   /api/decision")
	log.Println("      GET    /api/proposals/pending")
	log.Println("      GET    /api/health")

	if err := router.Run(":8080"); err != nil {
		log.Fatal("Failed to start server:", err)
	}
}
