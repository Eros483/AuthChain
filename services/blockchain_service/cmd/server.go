package main

import (
	"log"
	"os"

	"authchain/internal/api"
	"authchain/internal/chain"
	"authchain/internal/consensus"
	"authchain/internal/governance"
	"authchain/internal/validator"
)

func main() {
	proposalStore := governance.NewProposalStore()
	toolRegistry := governance.NewToolRegistry()

	ownerRegistry := governance.NewDirectoryOwnerRegistry()

	log.Println("AuthChain Blockchain Service Starting")

	if err := os.MkdirAll("./data", 0755); err != nil {
		log.Fatal("Failed to create data directory:", err)
	}

	blockchain, err := chain.LoadFromFile("./data/blockchain.json")
	if err != nil {
		log.Printf("Creating new blockchain: %v", err)
		blockchain = chain.NewBlockchain()
	}
	log.Printf("✓ Blockchain loaded (length: %d)", blockchain.Length())

	validatorRegistry := validator.NewValidatorRegistry()
	log.Printf("✓ Validator registry initialized (empty - add validators via API)")

	quorumConsensus := consensus.NewQuorumConsensus(validatorRegistry)
	log.Printf("✓ Consensus mechanism initialized")

	handler := api.NewHandler(
		proposalStore,
		toolRegistry,
		ownerRegistry,
		blockchain,
		quorumConsensus,
		validatorRegistry,
	)

	router := api.SetupRouter(handler)

	log.Println("Port: 8081")

	if err := router.Run(":8081"); err != nil {
		log.Fatal("Failed to start server:", err)
	}
}
