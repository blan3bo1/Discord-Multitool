"""
JavaScript injection module using Chrome DevTools Protocol
"""

import json
import time
import websocket
import requests
from .logger import get_logger

logger = get_logger()


class DiscordInjector:
    """Handles JavaScript injection into Discord using CDP"""
    
    def __init__(self, debug_port=9222, config=None):
        self.debug_port = debug_port
        self.config = config or {}
        self.ws = None
        self.target_id = None
        self.message_id = 1
    
    def connect(self):
        """Connect to Discord's DevTools"""
        try:
            # Get list of available targets
            response = requests.get(f"http://localhost:{self.debug_port}/json/list")
            targets = response.json()
            
            # Find the main Discord page target
            for target in targets:
                if target.get('type') == 'page' and 'discord' in target.get('url', '').lower():
                    self.target_id = target['id']
                    break
            
            if not self.target_id:
                logger.error("No Discord page target found")
                return False
            
            # Connect to WebSocket
            ws_url = f"ws://localhost:{self.debug_port}/devtools/page/{self.target_id}"
            self.ws = websocket.create_connection(ws_url)
            
            # Wait a moment for connection to stabilize
            time.sleep(1)
            
            logger.info(f"Connected to Discord (target: {self.target_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def _send_command(self, method, params=None):
        """Send CDP command with proper message ID"""
        if not self.ws:
            logger.error("WebSocket not connected")
            return None
        
        # Create command with integer ID
        command = {
            "id": self.message_id,
            "method": method
        }
        
        if params:
            command["params"] = params
        
        # Increment message ID for next command
        self.message_id += 1
        
        try:
            # Send command
            self.ws.send(json.dumps(command))
            
            # Receive response
            response = self.ws.recv()
            result = json.loads(response)
            
            # Check if we got an error response
            if 'error' in result:
                logger.error(f"CDP error: {result['error']}")
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None
    
    def inject_script(self, script_content):
        """Inject JavaScript into the page"""
        try:
            # First, enable Runtime domain
            logger.debug("Enabling Runtime domain...")
            runtime_response = self._send_command("Runtime.enable")
            if not runtime_response:
                logger.error("Failed to enable Runtime domain")
                return False
            
            # Wait a moment
            time.sleep(1)
            
            # Get execution contexts
            logger.debug("Getting execution contexts...")
            contexts_response = self._send_command("Runtime.getExecutionContexts")
            
            context_id = None
            if contexts_response and 'result' in contexts_response:
                contexts = contexts_response['result'].get('executionContexts', [])
                if contexts:
                    # Find the main frame context
                    for ctx in contexts:
                        if ctx.get('name') == '' or ctx.get('type') == 'default':
                            context_id = ctx.get('id')
                            break
                    if not context_id:
                        context_id = contexts[0].get('id')
                    logger.debug(f"Using execution context ID: {context_id}")
            
            # Prepare the script for injection
            # Escape the script properly
            escaped_script = json.dumps(script_content)
            
            # Create evaluation expression
            eval_expr = f"""
            (function() {{
                try {{
                    {script_content}
                    return {{success: true, message: 'Script executed successfully'}};
                }} catch(e) {{
                    return {{success: false, error: e.toString(), stack: e.stack}};
                }}
            }})();
            """
            
            # Prepare evaluation parameters
            eval_params = {
                "expression": eval_expr,
                "returnByValue": True,
                "awaitPromise": True
            }
            
            if context_id:
                eval_params["contextId"] = context_id
            
            # Execute the script
            logger.info("Injecting quest helper script...")
            eval_response = self._send_command("Runtime.evaluate", eval_params)
            
            if not eval_response:
                logger.error("No response from evaluation")
                return False
            
            # Check the result
            if 'result' in eval_response:
                result_data = eval_response['result']
                if 'result' in result_data:
                    result_value = result_data['result'].get('value', {})
                    if isinstance(result_value, dict):
                        if result_value.get('success'):
                            logger.info("✅ Script injection successful")
                            return True
                        else:
                            logger.error(f"Script execution error: {result_value.get('error')}")
                            return False
                elif 'subtype' in result_data and result_data['subtype'] == 'error':
                    logger.error(f"JavaScript error: {result_data.get('description')}")
                    return False
            
            logger.info("Script injected (no return value)")
            return True
            
        except Exception as e:
            logger.error(f"Injection failed: {e}")
            return False
    
    def close(self):
        """Close WebSocket connection"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
            logger.debug("Connection closed")