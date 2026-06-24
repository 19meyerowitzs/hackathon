"""
MCP Manager for handling Model Context Protocol configurations.
This module provides centralized management of MCP server configurations,
presets, and tool validation.
"""

import json
import os
import copy
import shutil
import sys
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.Omni_Helper.utils.logging_config import logger


class MCPManager:
    """
    Manages MCP (Model Context Protocol) server configurations.
    
    Features:
    - Load configurations from JSON file or read dict file
    - Validate MCP server availability and give information
    - Handle tool status and health checks
    """
    
    def __init__(self):
        """
        Initialize the MCP Manager.
        """
        self.config_file = None
        self.config_data = {}
        self.tool_status = {}  # Track tool health status

    
    def load_config(self, 
                 config_file: str | None = "mcp_config.json",
                 config_dict: dict = None
        ) -> bool:
        """
        Load MCP configuration from JSON file or provided dict
        
        Args:
            config_file: Path to the JSON configuration file
            config_dict: Configuration dictionary to use instead of file

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if config_file is None and config_dict is None:
            raise ValueError("Either config_file or config_dict must be provided, both cannot be None")

        try:
            if config_dict is not None:
                if 'mcp_servers' not in config_dict:
                    self.config_data['mcp_servers'] = config_dict
                elif 'mcp_servers' in config_dict:
                    self.config_data = config_dict

            else:
                self.config_file = config_file
                config_path = Path(self.config_file)
                if not config_path.exists():
                    raise FileExistsError("Config file not found")

                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                
            # Initialize tool status
            for tool_name in self.config_data.get('mcp_servers', {}):
                self.tool_status[tool_name] = {'status': 'unknown', 'last_check': None}
                # Update config_data with additional keys if they don't exist
                if 'enabled' not in self.config_data['mcp_servers'][tool_name]:
                    self.config_data['mcp_servers'][tool_name]['enabled'] = 'true'
                if 'category' not in self.config_data['mcp_servers'][tool_name]:
                    self.config_data['mcp_servers'][tool_name]['category'] = 'utilities'
            
            logger.info(f"Loading MCP config successfully!")
            return True
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            return False
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available MCP tools from configuration.
        
        Returns:
            Dict mapping tool names to their configurations
        """
        return self.config_data.get('mcp_servers', {})
    
    def get_enabled_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get only enabled MCP tools.
        
        Returns:
            Dict mapping enabled tool names to their configurations
        """
        all_tools = self.get_available_tools()
        return {
            name: config for name, config in all_tools.items()
            if config.get('enabled', False)
        }
    
    def get_tools_by_category(self) -> Dict[str, List[str]]:
        """
        Group tools by category.
        
        Returns:
            Dict mapping categories to lists of tool names
        """
        categories = {}
        for name, config in self.get_available_tools().items():
            category = config.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(name)
        return categories
    
    def get_all_tools_with_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all tools with their enabled status and validation.
        
        Returns:
            Dict mapping tool names to their full configuration including status
        """
        all_tools = self.get_available_tools()
        tools_with_status = {}
        
        for name, config in all_tools.items():
            is_valid, status_msg = self.validate_tool(name)
            tools_with_status[name] = {
                **config,
                'is_valid': is_valid,
                'status_message': status_msg,
                'enabled': config.get('enabled', False)
            }
        
        return tools_with_status
    
    def update_tool_enabled_status(self, tool_name: str, enabled: bool, save: bool = False) -> bool:
        """
        Update the enabled status of a tool in the configuration.
        
        Args:
            tool_name: Name of the tool
            enabled: Whether the tool should be enabled
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            if 'mcp_servers' in self.config_data and tool_name in self.config_data['mcp_servers']:
                self.config_data['mcp_servers'][tool_name]['enabled'] = enabled
                if save: 
                    self.save_config()
                return True
        except Exception as e:
            logger.error(f"Error updating tool status: {e}")
        return False
    
    def save_config(self) -> bool:
        """
        Save the current configuration back to the JSON file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            config_path = Path(self.config_file)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
   
    def validate_tool(self, tool_name: str) -> Tuple[bool, str]:
        """
        Validate if a tool is available and working.
        
        Args:
            tool_name: Name of the tool to validate
            
        Returns:
            Tuple of (is_valid, status_message)
        """
        all_tools = self.get_available_tools()
        if tool_name not in all_tools:
            return False, f"Tool '{tool_name}' not found in configuration"
        
        tool_config = all_tools[tool_name]
        
        # Check if the script file exists
        if tool_config['transport'] == 'stdio':
            script_path = Path(tool_config['args'][0])
            if not script_path.exists():
                return False, f"Script file not found: {script_path}"
        
        # Try to run a quick validation (if possible)
        try:
            # For stdio tools, we could try to start and immediately stop them
            # For now, just check file existence
            self.tool_status[tool_name] = {'status': 'available', 'last_check': 'now'}
            return True, "Tool is available"
        except Exception as e:
            self.tool_status[tool_name] = {'status': 'error', 'last_check': 'now'}
            return False, f"Tool validation failed: {e}"
      
    def get_tool_status(self, tool_name: str) -> Dict[str, Any]:
        """
        Get the current status of a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dict with status information
        """
        return self.tool_status.get(tool_name, {'status': 'unknown', 'last_check': None})
    
    def enable_tool(self, tool_name: str, save: bool = False) -> bool:
        """
        Enable a tool in the configuration.
        
        Args:
            tool_name: Name of the tool to enable
            
        Returns:
            bool: True if successful
        """
        if tool_name in self.config_data.get('mcp_servers', {}):
            self.config_data['mcp_servers'][tool_name]['enabled'] = True
            if save:
                return self._save_config()
            return True
        return False
    
    def disable_tool(self, tool_name: str, save: bool = False) -> bool:
        """
        Disable a tool in the configuration.
        
        Args:
            tool_name: Name of the tool to disable
            
        Returns:
            bool: True if successful
        """
        if tool_name in self.config_data.get('mcp_servers', {}):
            self.config_data['mcp_servers'][tool_name]['enabled'] = False
            if save:
                return self._save_config()
            return True
        return False
    
    def _save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            bool: True if saved successfully
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration.
        
        Returns:
            Dict with configuration statistics
        """
        all_tools = self.get_available_tools()
        enabled_tools = self.get_enabled_tools()
        
        return {
            'total_tools': len(all_tools),
            'enabled_tools': len(enabled_tools),
            'categories': list(self.get_tools_by_category().keys())
        }

    def create_mcp_server_config(self, transport_type, **kwargs):
        """
        Creates a configuration dictionary for MCP based on the specified transport type and parameters.

        Args:
            transport_type (str): The type of transport, either 'streamable_http' or 'stdio'.
            **kwargs: Arbitrary keyword arguments.
                'name' of the MCP.
                For 'streamable_http', requires 'url'.
                For 'stdio', requires 'command' and 'path'.

        Returns:
            dict: A configuration dictionary for the specified transport type.
        """
        config = {}
        if transport_type == "streamable_http":
            if "url" not in kwargs:
                raise ValueError("URL is required for streamable_http transport.")
            config[kwargs["name"]] = {
                "url": kwargs["url"],
                "transport": "streamable_http",
            }
    
        elif transport_type == "stdio":
            if "command" not in kwargs:
                raise ValueError("Command is required for stdio transport.")

            if "path" not in kwargs and "args" not in kwargs:
                raise ValueError("Either 'path' or 'args' is required for stdio transport.")
            
            command = kwargs["command"]
            if command == "python":  # Check if 'python' command is available in PATH
                if not shutil.which("python"):
                    # If 'python' is not available, use sys.executable instead
                    command = sys.executable

            args = []
            if "path" in kwargs:
                args.extend([kwargs["path"]] if not isinstance(kwargs["path"], list) else kwargs["path"])
            elif "args" in kwargs:
                args.extend([kwargs["args"]] if not isinstance(kwargs["args"], list) else kwargs["args"])

            config[kwargs["name"]] = {
                "command": command,
                "args": args,
                "transport": "stdio",
            }

        else:
            raise ValueError("Invalid transport type. Use 'streamable_http' or 'stdio'.")
        
        if self.config_data == {}:
            self.load_config(config_dict=copy.deepcopy(config))
        return config
