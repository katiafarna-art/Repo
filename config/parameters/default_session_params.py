"""Script contenente i parametri di configurazione di default per le logiche di retry sugli endpoints di servizio"""

from dataclasses import dataclass

DEFAULT_POOLSIZE = 100


@dataclass
class RetryDefaultConfig:
    http_retry = 3
    http_retry_backoff_factor = 30
    max_retry_init = 10
    max_retry_upload = 10
    max_retry_sync = 10
    max_retry_async = 10
    max_retry_status = 10
    max_retry_retrieve = 10
    max_retry_pipeline = 100
    sleep_default = 3
    sleep_retry = 2.5
