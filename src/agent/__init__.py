"""
Agente Recomendador de Campus Universitarios
Sistema de GraphRAG para Metro de Madrid
URJC 2025/2026
"""

from .recommender import MetroCampusRecommender
from .llm_interface import LLMInterface, OpenAIProvider, AnthropicProvider, LocalProvider

__all__ = [
    'MetroCampusRecommender',
    'LLMInterface',
    'OpenAIProvider',
    'AnthropicProvider',
    'LocalProvider'
]
