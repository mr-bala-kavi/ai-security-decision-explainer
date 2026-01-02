"""
LLM Client (OpenAI) for Generating Human-Readable Explanations

NOTE: This file now uses OpenAI API instead of Claude API.
The name is kept for backward compatibility with existing imports.
"""

# Import from the OpenAI client implementation
from src.llm_engine.openai_client import LLMExplainer, ClaudeExplainer

# For backward compatibility, alias ClaudeExplainer to LLMExplainer
__all__ = ['ClaudeExplainer', 'LLMExplainer']
