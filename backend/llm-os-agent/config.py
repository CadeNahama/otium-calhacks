#!/usr/bin/env python3

"""
Configuration management for LLM-OS Agent - Phase 1 Simplified (OpenAI Only)
"""
import os
import json

class Config:
    def __init__(self, config_path=None):
        self.config_path = config_path or "config.json"
        self.default_config = {
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False
            },
            "agent": {
                "log_level": "INFO"
            },
            "paths": {
                "logs_dir": "logs"
            },
            "ai": {
                "provider": "openai",
                "openai": {
                    "model": "gpt-3.5-turbo",
                    "api_key": "",
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
                return self.default_config
        else:
            # Create default config file
            self.save_config(self.default_config)
            return self.default_config
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config to {self.config_path}: {e}")
    
    def get(self, key, default=None):
        """Get configuration value using dot notation (e.g., 'ai.openai.model')"""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key, value):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()

# Global config instance
config = Config() 