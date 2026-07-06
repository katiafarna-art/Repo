"""Script contenente i parametri di configurazione di default per gli Splitter del servizio"""

from dataclasses import dataclass


@dataclass
class SplitterDefaultConfig:
    num_chunk: int = 10
    dpi: int = 250
    greyscale: bool = False
    start_page: int = 1
