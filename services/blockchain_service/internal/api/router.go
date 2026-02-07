package api

import (
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func SetupRouter(handler *Handler) *gin.Engine {
	router := gin.Default()

	router.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:3000", "http://localhost:5173", "http://localhost:8080", "https://auth-chain-kgij.vercel.app/"},
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
	}))

	api := router.Group("/api")
	{
		api.POST("/actions", handler.SubmitAction)
		api.POST("/blocks", handler.RecordDecision)

		api.GET("/blocks", handler.GetBlocks)
		api.GET("/blocks/:index", handler.GetBlock)
		api.GET("/blocks/proposal/:proposal_id", handler.GetBlockByProposal)

		api.POST("/verify", handler.VerifyChain)

		api.POST("/validators", handler.AddValidator)
		api.GET("/validators", handler.GetValidators)
		api.DELETE("/validators/:id", handler.RemoveValidator)

		api.GET("/health", handler.HealthCheck)
	}

	return router
}
