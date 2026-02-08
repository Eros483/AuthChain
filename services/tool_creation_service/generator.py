# deterministcally build tool boilerplate from LLM-generated function spec @ services/tool_creation_service/generator.py -----
from pydantic import BaseModel
from typing import Dict, Any, Literal, List
import json
from backend.core.llm_factory import get_llm
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class ToolCreationProposal(BaseModel):
    """Proposal for a new tool to be created"""
    tool_name: str
    description: str
    parameters: List[Dict[str, str]]
    implementation: str
    risk_tier: Literal["SAFE", "CRITICAL"]
    reasoning: str
    example_usage: str

    function_body: str = ""

class FunctionSpec(BaseModel):
    """LLM generates only this part"""
    function_name: str
    description: str
    parameters: List[Dict[str, str]]
    function_body: str
    risk_tier: Literal["SAFE", "CRITICAL"]
    reasoning: str

def generate_tool_proposal(task_description: str, context: str = "") -> ToolCreationProposal:
    """
    Uses LLM to generate function specification, then we wrap it deterministically
    
    Args:
        task_description: What capability the agent needs
        context: Recent conversation context for better understanding
    
    Returns:
        ToolCreationProposal with complete implementation
    """
    llm = get_llm()
    
    # Step 1: Get structured specification from LLM
    prompt = f"""You are generating a Python function specification.

TASK: {task_description}

CONTEXT: {context}

You must respond with ONLY a JSON object (no markdown, no explanation) with this EXACT structure:

{{
    "function_name": "descriptive_snake_case_name",
    "description": "One-line description of what the function does",
    "parameters": [
        {{"name": "param1", "type": "float", "description": "What this parameter represents"}},
        {{"name": "param2", "type": "int", "description": "What this parameter represents"}}
    ],
    "function_body": "    # Function implementation here\\n    try:\\n        result = param1 * param2\\n        return f'Result: {{result}}'\\n    except Exception as e:\\n        return f'ERROR: {{str(e)}}'",
    "risk_tier": "SAFE",
    "reasoning": "This tool is needed because..."
}}

CRITICAL RULES FOR function_body:
1. Use 4-space indentation (the code will go inside a function)
2. ALWAYS include try/except error handling
3. Return a descriptive string message
4. Include ACTUAL implementation logic (no TODO comments)
5. Use the parameter names from the "parameters" list
6. Keep it simple and focused on the task

PARAMETER TYPES (choose from):
- "str" for text
- "int" for whole numbers  
- "float" for decimal numbers
- "bool" for true/false
- "list" for arrays
- "dict" for objects

RISK CLASSIFICATION:
- SAFE: Pure computation, data processing, no external effects
- CRITICAL: File I/O, database access, network calls, system commands

Example for "convert celsius to fahrenheit":
{{
    "function_name": "convert_celsius_to_fahrenheit",
    "description": "Converts temperature from Celsius to Fahrenheit",
    "parameters": [
        {{"name": "celsius", "type": "float", "description": "Temperature in Celsius"}}
    ],
    "function_body": "    try:\\n        fahrenheit = (celsius * 9/5) + 32\\n        return f'{{celsius}}°C equals {{fahrenheit:.2f}}°F'\\n    except Exception as e:\\n        return f'ERROR: {{str(e)}}'",
    "risk_tier": "SAFE",
    "reasoning": "Needed to perform temperature unit conversions"
}}

Now generate the specification for: {task_description}

Respond with ONLY the JSON object:"""

    response = llm.invoke(prompt)
    content = response.content if hasattr(response, 'content') else str(response)

    try:
        content = content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        if not content.startswith('{'):
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                content = content[start:end]
        
        spec_data = json.loads(content.strip())
        spec = FunctionSpec(**spec_data)
        
        logger.info(f"LLM generated spec for: {spec.function_name}")
        
    except Exception as e:
        logger.error(f"Failed to parse LLM response: {e}")
        logger.error(f"Response was: {content[:500]}")
        raise ValueError(f"LLM did not return valid JSON: {e}")

    complete_implementation = _build_complete_tool(spec)

    proposal = ToolCreationProposal(
        tool_name=spec.function_name,
        description=spec.description,
        parameters=spec.parameters,
        implementation=complete_implementation,
        risk_tier=spec.risk_tier,
        reasoning=spec.reasoning,
        example_usage=_generate_example_usage(spec),
        function_body=spec.function_body
    )
    
    return proposal

def _build_complete_tool(spec: FunctionSpec) -> str:
    """
    Deterministically builds complete tool code from specification
    """
    params = []
    for param in spec.parameters:
        param_name = param['name']
        param_type = param['type']
        params.append(f"{param_name}: {param_type}")
    
    param_signature = ", ".join(params)

    docstring_lines = [
        f'    """',
        f'    {spec.description}',
        f'    '
    ]
    
    if spec.parameters:
        docstring_lines.append('    Args:')
        for param in spec.parameters:
            docstring_lines.append(f'        {param["name"]}: {param["description"]}')
        docstring_lines.append('    ')
    
    docstring_lines.extend([
        '    Returns:',
        '        Result message as string',
        '    """'
    ])
    
    docstring = "\n".join(docstring_lines)

    implementation = f"""from langchain_core.tools import tool

@tool
def {spec.function_name}({param_signature}) -> str:
{docstring}
{spec.function_body}
"""
    
    return implementation

def _generate_example_usage(spec: FunctionSpec) -> str:
    """
    Generates example usage string
    """
    params = []
    for param in spec.parameters:
        param_name = param['name']
        param_type = param['type']
        
        # Generate example values
        if param_type == "str":
            value = f'"{param_name}_value"'
        elif param_type == "int":
            value = "42"
        elif param_type == "float":
            value = "3.14"
        elif param_type == "bool":
            value = "True"
        elif param_type == "list":
            value = "[1, 2, 3]"
        elif param_type == "dict":
            value = '{"key": "value"}'
        else:
            value = f'"{param_name}"'
        
        params.append(f"{param_name}={value}")
    
    return f"{spec.function_name}({', '.join(params)})"

def validate_tool_code(code: str, risk_tier: str) -> Dict[str, Any]:
    """
    Performs static analysis on generated tool code
    
    Returns:
        {"safe": bool, "issues": [str], "warnings": [str]}
    """
    issues = []
    warnings = []
    
    # Check for dangerous patterns
    dangerous_patterns = [
        ("subprocess", "Shell command execution"),
        ("os.system", "Shell command execution"),
        ("eval(", "Code evaluation"),
        ("exec(", "Code execution"),
        ("__import__", "Dynamic imports"),
    ]
    
    for pattern, description in dangerous_patterns:
        if pattern in code:
            issues.append(f"Dangerous pattern detected: {description} ({pattern})")
    
    # Check for network calls
    network_patterns = ["requests.", "urllib.", "http.client", "socket."]
    has_network = any(pattern in code for pattern in network_patterns)
    
    if has_network and risk_tier != "CRITICAL":
        issues.append("Network calls require CRITICAL risk tier")
    
    # Check for file operations
    file_patterns = ["open(", "with open", "os.remove", "shutil."]
    has_file_ops = any(pattern in code for pattern in file_patterns)
    
    if has_file_ops and risk_tier != "CRITICAL":
        issues.append("File operations require CRITICAL risk tier")
    
    # Syntax validation
    try:
        compile(code, '<generated_tool>', 'exec')
    except SyntaxError as e:
        issues.append(f"Syntax error: {e}")
    
    # Check structure
    if "@tool" not in code:
        issues.append("Missing @tool decorator")
    
    if "def " not in code:
        issues.append("Missing function definition")
    
    if "return" not in code:
        warnings.append("Function may not return a value")
    
    return {
        "safe": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }