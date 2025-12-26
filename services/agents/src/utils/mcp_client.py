"""MCP Client for calling MCP servers from Python."""

import json
import logging
import os
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for calling Model Context Protocol servers."""
    
    def __init__(self, project_root: str = None):
        """Initialize MCP client.
        
        Args:
            project_root: Path to project root (defaults to auto-detect)
        """
        if project_root is None:
            # Auto-detect project root (go up from this file)
            current_file = os.path.abspath(__file__)
            # services/agents/src/utils/mcp_client.py -> go up 5 levels
            self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file)))))
        else:
            self.project_root = project_root
        
        logger.info(f"MCPClient initialized with project root: {self.project_root}")
    
    def call_tool(
        self,
        server: str,
        tool: str,
        arguments: Dict[str, Any],
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Call a tool on an MCP server.
        
        Args:
            server: Server name (e.g., 'zoho-mail', 'zoom')
            tool: Tool name (e.g., 'list_emails')
            arguments: Tool arguments
            env: Environment variables (e.g., {'ZOHO_ACCESS_TOKEN': 'abc123'})
        
        Returns:
            Dict with 'success', 'data', and optional 'error' keys
        """
        server_path = os.path.join(self.project_root, "mcp-servers", server, "src", "index.ts")
        
        if not os.path.exists(server_path):
            logger.error(f"MCP server not found at {server_path}")
            return {
                "success": False,
                "error": f"MCP server '{server}' not found",
                "data": None
            }
        
        # Prepare environment
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
            logger.info(f"Calling {server}/{tool} with custom env vars: {list(env.keys())}")
        
        # Build JSON-RPC request for tool call
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool,
                "arguments": arguments
            }
        }
        
        try:
            # Spawn MCP server process
            process = subprocess.Popen(
                ["npx", "tsx", server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=run_env,
                cwd=os.path.dirname(server_path)
            )
            
            # Send request
            request_json = json.dumps(request) + "\n"
            stdout, stderr = process.communicate(input=request_json.encode(), timeout=30)
            
            # Parse response
            if stderr:
                logger.debug(f"MCP server stderr: {stderr.decode()}")
            
            # Find JSON-RPC response in stdout
            for line in stdout.decode().split('\n'):
                line = line.strip()
                if line and line.startswith('{'):
                    try:
                        response = json.loads(line)
                        if 'result' in response:
                            result = response['result']
                            # Extract text content from MCP response
                            if 'content' in result and len(result['content']) > 0:
                                content = result['content'][0]
                                if content.get('type') == 'text':
                                    return {
                                        "success": not result.get('isError', False),
                                        "data": content.get('text'),
                                        "error": None
                                    }
                            return {
                                "success": True,
                                "data": result,
                                "error": None
                            }
                        elif 'error' in response:
                            return {
                                "success": False,
                                "data": None,
                                "error": response['error'].get('message', 'Unknown error')
                            }
                    except json.JSONDecodeError:
                        continue
            
            logger.error(f"No valid JSON-RPC response from {server}/{tool}")
            return {
                "success": False,
                "error": "No valid response from MCP server",
                "data": None
            }
        
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout calling {server}/{tool}")
            process.kill()
            return {
                "success": False,
                "error": "Request timeout",
                "data": None
            }
        except Exception as e:
            logger.error(f"Error calling {server}/{tool}: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }


# Global instance
mcp_client = MCPClient()
