import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Use mock APIs for hackathon testing without keys
    USE_MOCK_APIS: bool = os.environ.get("USE_MOCK_APIS", "false").lower() == "true"
    
    # Source Model (Original Codebase)
    SOURCE_MODEL: str = os.environ.get("SOURCE_MODEL", "gpt-3.5-turbo")
    SOURCE_API_KEY: str = os.environ.get("SOURCE_API_KEY", "")
    SOURCE_BASE_URL: str = os.environ.get("SOURCE_BASE_URL", "https://api.openai.com/v1")

    # Target Model (Where we are migrating to)
    TARGET_PROVIDER: str = os.environ.get("TARGET_PROVIDER", "NVIDIA NIM")
    TARGET_MODEL: str = os.environ.get("TARGET_MODEL", "meta/llama-3.3-70b-instruct")
    TARGET_BASE_URL: str = os.environ.get("TARGET_BASE_URL", "https://integrate.api.nvidia.com/v1")
    TARGET_API_KEY_ENV_VAR: str = os.environ.get("TARGET_API_KEY_ENV_VAR", "NVIDIA_API_KEY")
    TARGET_API_KEY: str = os.environ.get("TARGET_API_KEY", "")

    # Judge (Evaluator)
    JUDGE_MODEL: str = os.environ.get("JUDGE_MODEL", "gemini-2.0-flash")
    JUDGE_API_KEY: str = os.environ.get("JUDGE_API_KEY", "")

    # Optimizer (Prompt Translator)
    OPTIMIZER_MODEL: str = os.environ.get("OPTIMIZER_MODEL", "llama3-70b-8192")
    OPTIMIZER_API_KEY: str = os.environ.get("OPTIMIZER_API_KEY", "")

    # Optimization Rules
    OPTIMIZATION_THRESHOLD: int = int(os.environ.get("OPTIMIZATION_THRESHOLD", "90"))
    OPTIMIZATION_MAX_ITERATIONS: int = int(os.environ.get("OPTIMIZATION_MAX_ITERATIONS", "5"))

config = Config()
