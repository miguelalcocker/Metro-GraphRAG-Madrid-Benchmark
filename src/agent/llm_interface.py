#!/usr/bin/env python3
"""
Interfaz Genérica para LLMs
Soporta: OpenAI, Anthropic, Modelos Locales
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class LLMInterface(ABC):
    """Interfaz abstracta para proveedores de LLM"""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Genera una respuesta dado un prompt"""
        pass


class OpenAIProvider(LLMInterface):
    """Proveedor de OpenAI (GPT-4, GPT-3.5, etc.)"""

    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        """
        Inicializa el proveedor de OpenAI

        Args:
            model: Nombre del modelo (gpt-4, gpt-3.5-turbo, etc.)
            api_key: API key de OpenAI (si no se provee, usa variable de entorno)
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no configurada")

        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("Instala openai: pip install openai")

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000, **kwargs) -> str:
        """Genera respuesta usando OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en el Metro de Madrid y universidades."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"ERROR: {str(e)}"


class AnthropicProvider(LLMInterface):
    """Proveedor de Anthropic (Claude)"""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None):
        """
        Inicializa el proveedor de Anthropic

        Args:
            model: Nombre del modelo Claude
            api_key: API key de Anthropic
        """
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("Instala anthropic: pip install anthropic")

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000, **kwargs) -> str:
        """Genera respuesta usando Claude"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system="Eres un asistente experto en el Metro de Madrid y universidades.",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"ERROR: {str(e)}"


class LocalProvider(LLMInterface):
    """Proveedor de modelo local (Ollama, llama.cpp, etc.)"""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        """
        Inicializa el proveedor local

        Args:
            model: Nombre del modelo local
            base_url: URL del servidor local (Ollama por defecto)
        """
        self.model = model
        self.base_url = base_url

        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("Instala requests: pip install requests")

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000, **kwargs) -> str:
        """Genera respuesta usando modelo local (Ollama)"""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            response = self.requests.post(url, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except Exception as e:
            return f"ERROR: {str(e)}"


class MockProvider(LLMInterface):
    """Proveedor simulado para testing (sin API)"""

    def __init__(self):
        """Inicializa el proveedor mock"""
        self.call_count = 0

    def generate(self, prompt: str, **kwargs) -> str:
        """Genera respuesta simulada"""
        self.call_count += 1

        # Detectar tipo de consulta y dar respuestas predefinidas
        if "baseline" in prompt.lower() or "sin contexto" in prompt.lower():
            return """Para llegar desde Sol hasta un campus con Máster en Inteligencia Artificial,
puedes tomar la Línea 6 hasta Ciudad Universitaria, donde la UCM ofrece este programa.
El trayecto es directo y tarda aproximadamente 20 minutos."""

        elif "graphrag" in prompt.lower() or "contexto" in prompt.lower():
            # Simula respuesta con datos estructurados
            return """Basándome en los datos proporcionados:

**Mejor opción: Ciudad Universitaria (UCM)**
- Ruta: Sol → Cuatro Caminos (L1) → Transbordo → Ciudad Universitaria (L6)
- Distancia: 8 estaciones
- Transbordos: 1 (en Cuatro Caminos)
- Tiempo estimado: 22 minutos
- Estudios: Máster en Inteligencia Artificial (60 ECTS)

**Alternativa: Campus de Moncloa (UPM)**
- Ruta: Sol → Callao (L3) → Moncloa
- Distancia: 6 estaciones
- Transbordos: 0
- Tiempo estimado: 15 minutos"""

        else:
            return f"[MOCK] Respuesta simulada para pruebas (llamada #{self.call_count})"


def create_llm_provider(provider_type: str = "mock", **kwargs) -> LLMInterface:
    """
    Factory para crear proveedores de LLM

    Args:
        provider_type: Tipo de proveedor (openai, anthropic, local, mock)
        **kwargs: Argumentos específicos del proveedor

    Returns:
        Instancia de LLMInterface
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "local": LocalProvider,
        "mock": MockProvider
    }

    provider_class = providers.get(provider_type.lower())
    if not provider_class:
        raise ValueError(f"Proveedor desconocido: {provider_type}. Opciones: {list(providers.keys())}")

    return provider_class(**kwargs)
