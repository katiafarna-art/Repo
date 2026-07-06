DEFAULT_MODEL = {
    "openai": "gpt-5.1",
    "gemini": "gemini-2.5-flash"
}

DEFAULT_DESCRIPTION_EXPECTED_ETA = 5

model_to_eta = {
    "gpt-4.1-2025-04-14": 3.5,
    "gpt-4o": 4,
    "gpt-4o-2024-11-20": 5.5,
    "gpt-4o-2024-08-06": 4,
    "gpt-4o-mini": 35,
    "gemini-pro": DEFAULT_DESCRIPTION_EXPECTED_ETA,
    "gemini-flash": 3,
    "gemini-2.5-pro": 12,
    "gemini-2.5-flash": 8,
    "gemini-2.0-flash-001": 5,
    "gemini-2.0-flash-lite-001": 3,
    "gemini-1.5-pro-002": DEFAULT_DESCRIPTION_EXPECTED_ETA
}
