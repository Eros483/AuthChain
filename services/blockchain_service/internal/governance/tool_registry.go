package governance

type ToolRegistry struct {
	CriticalTools map[string]bool
}

func NewToolRegistry() *ToolRegistry {
	return &ToolRegistry{
		CriticalTools: map[string]bool{
			"write_file":           true,
			"delete_file":          true,
			"deploy_to_production": true,
			"delete_database":      true,
			"sql_db_query":         true,
			"git_push_commit":      true,
		},
	}
}

func (tr *ToolRegistry) IsCritical(tool string) bool {
	return tr.CriticalTools[tool]
}
