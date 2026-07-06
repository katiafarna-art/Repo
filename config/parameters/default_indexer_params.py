"""Script contenente i parametri di configurazione di default per gli Embedder adibiti a RAG"""

from dataclasses import dataclass


@dataclass
class EmbedderDefaultConfig:
    top_n: int = 3  # max numero di immagini da usare per similarità


@dataclass
class AdaEmbedderDefaultConfig:
    chunk_chars: int = 30000  # max tokens per ada embedding = 8000 -> about 30000 chars


@dataclass
class ISPEmbedderDefaultConfig:
    chunk_chars: int = 1500  # max tokens per e5 large embedding = 512 -> about 2000 chars
