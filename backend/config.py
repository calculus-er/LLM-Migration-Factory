import os
from pathlib import Path
from dotenv import load_dotenv

# Always override existing env vars on reload so hot-restart picks up .env changes
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path, override=True)

class Config:
    # Use mock APIs for hackathon testing without keys
    USE_MOCK_APIS: bool = os.environ.get("USE_MOCK_APIS", "false").lower() == "true"
    
    # Source Model (Original Codebase — the code being migrated away from)
    SOURCE_MODEL: str = os.environ.get("SOURCE_MODEL", "openai/gpt-oss-20b")
    SOURCE_API_KEY: str = os.environ.get("SOURCE_API_KEY", "")
    SOURCE_BASE_URL: str = os.environ.get("SOURCE_BASE_URL", "https://api.groq.com/openai/v1")

    # Target Model (Where we are migrating to)
    TARGET_PROVIDER: str = os.environ.get("TARGET_PROVIDER", "Groq Llama")
    TARGET_MODEL: str = os.environ.get("TARGET_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    TARGET_BASE_URL: str = os.environ.get("TARGET_BASE_URL", "https://api.groq.com/openai/v1")
    TARGET_API_KEY_ENV_VAR: str = os.environ.get("TARGET_API_KEY_ENV_VAR", "GROQ_API_KEY")
    TARGET_API_KEY: str = os.environ.get("TARGET_API_KEY", "")

    # Judge (Evaluator — scores the target output against golden truth)
    JUDGE_MODEL: str = os.environ.get("JUDGE_MODEL", "openai/gpt-oss-120b")
    JUDGE_API_KEY: str = os.environ.get("JUDGE_API_KEY", "")
    JUDGE_BASE_URL: str = os.environ.get("JUDGE_BASE_URL", "https://api.groq.com/openai/v1")

    # Optimizer (Prompt Translator — rewrites prompts for the target model)
    OPTIMIZER_MODEL: str = os.environ.get("OPTIMIZER_MODEL", "llama-3.3-70b-versatile")
    OPTIMIZER_API_KEY: str = os.environ.get("OPTIMIZER_API_KEY", "")
    OPTIMIZER_BASE_URL: str = os.environ.get("OPTIMIZER_BASE_URL", "https://api.groq.com/openai/v1")

    # Optimization Rules
    OPTIMIZATION_THRESHOLD: int = int(os.environ.get("OPTIMIZATION_THRESHOLD", "90"))
    OPTIMIZATION_MAX_ITERATIONS: int = int(os.environ.get("OPTIMIZATION_MAX_ITERATIONS", "5"))

    # Rough USD per 1k tokens for target-side cost estimate in reports
    TARGET_COST_INPUT_PER_1K: float = float(os.environ.get("TARGET_COST_INPUT_PER_1K", "0.0003"))
    TARGET_COST_OUTPUT_PER_1K: float = float(os.environ.get("TARGET_COST_OUTPUT_PER_1K", "0.0006"))

    # UI labels (optional; default to model ids)
    SOURCE_LABEL: str = os.environ.get("SOURCE_LABEL", "").strip() or os.environ.get("SOURCE_MODEL", "source")
    TARGET_LABEL: str = os.environ.get("TARGET_LABEL", "").strip() or os.environ.get("TARGET_MODEL", "target")
    JUDGE_LABEL: str = os.environ.get("JUDGE_LABEL", "").strip() or os.environ.get("JUDGE_MODEL", "judge")
    OPTIMIZER_LABEL: str = os.environ.get("OPTIMIZER_LABEL", "").strip() or os.environ.get("OPTIMIZER_MODEL", "optimizer")

    # CORS: comma-separated origins; see main.py
    @staticmethod
    def allowed_origins() -> list[str]:
        raw = os.environ.get(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,"
            "http://localhost:5174,http://127.0.0.1:5174,"
            "http://localhost:5175,http://127.0.0.1:5175",
        )
        return [o.strip() for o in raw.split(",") if o.strip()]


config = Config()
