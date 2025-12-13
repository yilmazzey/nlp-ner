"""
Ollama API client for local LLM models (Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.3).
"""

import requests
import yaml
import os
import time
from typing import Optional


def load_config():
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class OllamaClient:
    """Client for Ollama API (local LLM inference)"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Ollama client.
        
        Args:
            base_url (str, optional): Ollama API base URL. If None, loads from config.
        """
        config = load_config()
        self.base_url = base_url or config.get('ollama', {}).get('base_url', 'http://localhost:11434')
        self.api_url = f"{self.base_url}/api/generate"
        
        # Default models
        self.available_models = config.get('ollama', {}).get('models', [
            'llama3.1:8b-instruct',
            'mistral:7b-instruct-v0.3'
        ])
        self.default_model = self.available_models[0]
    
    def generate(self, prompt: str, model_name: Optional[str] = None, max_retries: int = 3, retry_delay: int = 2):
        """
        Generate text using Ollama API.
        
        Args:
            prompt (str): Input prompt
            model_name (str, optional): Model name. If None, uses default.
            max_retries (int): Maximum number of retry attempts
            retry_delay (int): Delay between retries in seconds
        
        Returns:
            str: Generated text response
        """
        model = model_name or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,  # Deterministic output
                "num_predict": 2000
            }
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, json=payload, timeout=120)
                response.raise_for_status()
                
                result = response.json()
                return result.get('response', '').strip()
            
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    print(f"Cannot connect to Ollama at {self.base_url}. Make sure Ollama is running.")
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise ConnectionError(
                        f"Cannot connect to Ollama at {self.base_url}. "
                        "Please ensure Ollama is installed and running. "
                        "Visit https://ollama.ai for installation instructions."
                    )
            
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"Request timeout. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise TimeoutError("Ollama request timed out after multiple retries")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise
    
    def is_available(self) -> bool:
        """
        Check if Ollama is available.
        
        Returns:
            bool: True if Ollama server is reachable
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self):
        """
        List available models in Ollama.
        
        Returns:
            list: List of available model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except:
            return []


if __name__ == "__main__":
    # Test the client
    try:
        client = OllamaClient()
        if client.is_available():
            print(f"Available models: {client.list_models()}")
            response = client.generate("Say 'Hello, World!'")
            print(f"Response: {response}")
        else:
            print("Ollama is not available. Make sure it's running at http://localhost:11434")
    except Exception as e:
        print(f"Error: {e}")


