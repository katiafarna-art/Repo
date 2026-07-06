"""Instantiate and configure a recurrent request session"""

import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from config.parameters import RetryDefaultConfig, DEFAULT_POOLSIZE


retry_strategy = Retry(
    total=RetryDefaultConfig.http_retry,
    backoff_factor=RetryDefaultConfig.http_retry_backoff_factor,
)

session = requests.Session()
adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=DEFAULT_POOLSIZE,
    pool_maxsize=DEFAULT_POOLSIZE,
)
session.mount("http://", adapter)
session.mount("https://", adapter)
