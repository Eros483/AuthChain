// blockchain-service/cmd/server.go
package main

import (
	"log"
	"os"

	"authchain/internal/api"
	"authchain/internal/chain"
	"authchain/internal/consensus"
	"authchain/internal/validator"
)

func main() {
	log.Println("AuthChain Blockchain Service Starting")

	if err := os.MkdirAll("./services/blockchain_service/data", 0755); err != nil {
		log.Fatal("Failed to create data directory:", err)
	}

	blockchain, err := chain.LoadFromFile("./services/blockchain_service/data/blockchain.json")
	if err != nil {
		log.Printf("Creating new blockchain: %v", err)
		blockchain = chain.NewBlockchain()
	}
	log.Printf("✓ Blockchain loaded (length: %d)", blockchain.Length())

	validatorRegistry := validator.NewValidatorRegistry()
	log.Printf("✓ Validator registry initialized (empty - add validators via API)")

	quorumConsensus := consensus.NewQuorumConsensus(validatorRegistry)
	log.Printf("✓ Consensus mechanism initialized")

	handler := api.NewHandler(blockchain, quorumConsensus, validatorRegistry)
	router := api.SetupRouter(handler)

	log.Println("Port: 8081")
	log.Println("")
	log.Println("Endpoints:")
	log.Println("   Blocks:")
	log.Println("      POST   /api/blocks")
	log.Println("      GET    /api/blocks")
	log.Println("      GET    /api/blocks/:index")
	log.Println("      GET    /api/blocks/proposal/:proposal_id")
	log.Println("")
	log.Println("   Validators:")
	log.Println("      POST   /api/validators")
	log.Println("      GET    /api/validators")
	log.Println("      DELETE /api/validators/:id")
	log.Println("")
	log.Println("   System:")
	log.Println("      POST   /api/verify")
	log.Println("      GET    /api/health")
	log.Println("")
	log.Println("NOTE: Add at least 1 validator before recording decisions")

	if err := router.Run(":8081"); err != nil {
		log.Fatal("Failed to start server:", err)
	}
}
