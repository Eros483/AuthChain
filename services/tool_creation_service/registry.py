# ----- Manages persistence and dynamic loading of created tools. @ services/tool_creation_service/registry.py -----

import os
import hashlib
from typing import List, Dict, Any
from datetime import datetime
import json
from langchain_core.tools import BaseTool

from backend.utils.logger import get_logger
from services.tool_creation_service.generator import ToolCreationProposal

logger = get_logger(__name__)

TOOLS_DIR = "./services/tool_creation_service/generated_tools"
REGISTRY_FILE = os.path.join(TOOLS_DIR, "registry.json")

os.makedirs(TOOLS_DIR, exist_ok=True)

class DynamicToolRegistry:
    """Manages dynamically created tools"""
    
    def __init__(self):
        self.registry = self._load_registry()
        self.loaded_tools: Dict[str, BaseTool] = {}
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from disk"""
        if os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE, 'r') as f:
                return json.load(f)
        return {"tools": {}}
    
    def _save_registry(self):
        """Persist registry to disk"""
        with open(REGISTRY_FILE, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def register_tool(self, proposal: 'ToolCreationProposal', approved_by: str) -> str:
        """
        Registers an approved tool and saves it to disk
        
        Args:
            proposal: Tool creation proposal
            approved_by: Username of approver
        
        Returns:
            tool_hash: Unique identifier for blockchain logging
        """
        # Generate unique hash for the tool
        tool_hash = hashlib.sha256(
            proposal.implementation.encode()
        ).hexdigest()[:16]
        
        # Create tool file
        tool_filename = f"{proposal.tool_name}_{tool_hash}.py"
        tool_filepath = os.path.join(TOOLS_DIR, tool_filename)
        
        # Write tool implementation to file
        with open(tool_filepath, 'w') as f:
            f.write(f"""# Auto-generated tool: {proposal.tool_name}
# Created: {datetime.now().isoformat()}
# Approved by: {approved_by}
# Risk Tier: {proposal.risk_tier}

{proposal.implementation}
""")
        
        # Update registry
        self.registry["tools"][proposal.tool_name] = {
            "hash": tool_hash,
            "filepath": tool_filepath,
            "description": proposal.description,
            "risk_tier": proposal.risk_tier,
            "parameters": proposal.parameters,
            "created_at": datetime.now().isoformat(),
            "approved_by": approved_by,
            "reasoning": proposal.reasoning
        }
        
        self._save_registry()
        
        logger.info(f"Registered tool: {proposal.tool_name} (hash: {tool_hash})")
        
        return tool_hash
    
    def load_tool(self, tool_name: str) -> BaseTool:
        """
        Dynamically imports and returns a tool by name
        
        Args:
            tool_name: Name of the tool to load
        
        Returns:
            BaseTool: The loaded tool
        """
        if tool_name in self.loaded_tools:
            return self.loaded_tools[tool_name]
        
        if tool_name not in self.registry["tools"]:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        
        tool_info = self.registry["tools"][tool_name]
        filepath = tool_info["filepath"]
        
        # Dynamic import
        import importlib.util
        spec = importlib.util.spec_from_file_location(tool_name, filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find the @tool decorated function
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, BaseTool):
                self.loaded_tools[tool_name] = attr
                logger.info(f"Loaded tool: {tool_name}")
                return attr
        
        raise ValueError(f"No tool found in {filepath}")
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns all registered tools"""
        return [
            {
                "name": name,
                **info
            }
            for name, info in self.registry["tools"].items()
        ]
    
    def get_all_tools(self) -> List[BaseTool]:
        """Loads and returns all registered tools"""
        tools = []
        for tool_name in self.registry["tools"].keys():
            try:
                tools.append(self.load_tool(tool_name))
            except Exception as e:
                logger.error(f"Failed to load tool {tool_name}: {e}")
        return tools

tool_registry = DynamicToolRegistry()