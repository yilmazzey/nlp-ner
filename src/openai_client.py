"""
OpenAI API client for GPT-4o and GPT-4o-mini models.
"""

import openai
import yaml
import os
import time
from typing import Optional


def load_config():
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class OpenAIClient:
    """Client for OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.
        
        Args:
            api_key (str, optional): OpenAI API key. If None, loads from config.
        """
        config = load_config()
        self.api_key = api_key or config.get('openai', {}).get('api_key', '')
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set it in configs/config.yaml")
        
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Default model
        self.default_model = config.get('openai', {}).get('models', ['gpt-4o'])[0]
    
    def generate(self, prompt: str, model_name: Optional[str] = None, max_retries: int = 3, retry_delay: int = 2):
        """
        Generate text using OpenAI API.
        
        Args:
            prompt (str): Input prompt
            model_name (str, optional): Model name. If None, uses default.
            max_retries (int): Maximum number of retry attempts
            retry_delay (int): Delay between retries in seconds
        
        Returns:
            str: Generated text response
        """
        model = model_name or self.default_model
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,  # Deterministic output
                    max_tokens=2000
                )
                
                return response.choices[0].message.content.strip()
            
            except openai.RateLimitError:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    raise
            
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise
    
    def is_available(self) -> bool:
        """
        Check if OpenAI API is available.
        
        Returns:
            bool: True if API key is set
        """
        return bool(self.api_key)


if __name__ == "__main__":
    # Test the client
    try:
        client = OpenAIClient()
        if client.is_available():
            response = client.generate("Say 'Hello, World!'")
            print(f"Response: {response}")
        else:
            print("OpenAI API key not configured")
    except Exception as e:
        print(f"Error: {e}")


