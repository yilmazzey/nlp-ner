"""
Google Gemini API client for Gemini 1.5 Flash model.
"""

import google.generativeai as genai
import yaml
import os
import time
from typing import Optional


def load_config():
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class GeminiClient:
    """Client for Google Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key (str, optional): Google AI API key. If None, loads from config.
        """
        config = load_config()
        self.api_key = api_key or config.get('google_ai', {}).get('api_key', '')
        
        if not self.api_key:
            raise ValueError("Google AI API key not found. Please set it in configs/config.yaml")
        
        genai.configure(api_key=self.api_key)
        
        # Default model
        self.default_model = config.get('google_ai', {}).get('models', ['gemini-1.5-flash'])[0]
        self.model = genai.GenerativeModel(self.default_model)
    
    def generate(self, prompt: str, model_name: Optional[str] = None, max_retries: int = 3, retry_delay: int = 2):
        """
        Generate text using Gemini API.
        
        Args:
            prompt (str): Input prompt
            model_name (str, optional): Model name. If None, uses default.
            max_retries (int): Maximum number of retry attempts
            retry_delay (int): Delay between retries in seconds
        
        Returns:
            str: Generated text response
        """
        # If different model specified, create new model instance
        if model_name and model_name != self.default_model:
            model = genai.GenerativeModel(model_name)
        else:
            model = self.model
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.0,  # Deterministic output
                        max_output_tokens=2000
                    )
                )
                
                return response.text.strip()
            
            except Exception as e:
                if attempt < max_retries - 1:
                    error_msg = str(e).lower()
                    if 'quota' in error_msg or 'rate' in error_msg:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        print(f"Error: {e}. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                else:
                    raise
    
    def is_available(self) -> bool:
        """
        Check if Gemini API is available.
        
        Returns:
            bool: True if API key is set
        """
        return bool(self.api_key)


if __name__ == "__main__":
    # Test the client
    try:
        client = GeminiClient()
        if client.is_available():
            response = client.generate("Say 'Hello, World!'")
            print(f"Response: {response}")
        else:
            print("Google AI API key not configured")
    except Exception as e:
        print(f"Error: {e}")


