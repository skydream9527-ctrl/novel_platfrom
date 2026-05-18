from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
NLSQL_DIR = PROJECT_ROOT / "nl-sql"
NLSQL_REFERENCE_DIR = NLSQL_DIR / "reference"
NLSQL_SCRIPT = NLSQL_DIR / "scripts" / "nl-sql.py"
OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

BUSINESS_LINES = {
    "browser-main": {
        "name": "浏览器主端",
        "reference_dir": "browser-main",
    },
    "browser-feed": {
        "name": "浏览器信息流",
        "reference_dir": "browser-feed",
    },
    "content-center": {
        "name": "内容中心",
        "reference_dir": "content-center",
    },
    "search": {
        "name": "搜索",
        "reference_dir": "search",
    },
    "novel": {
        "name": "小说",
        "reference_dir": "novel",
    },
}

API_BASE_URL = "http://model.mify.ai.srv/v1/"
API_KEY = "sk-XitB8gnr2LxiqNM9AuyKSmksl1Wc1riTaFMLPobQtN6AenAA"

MODEL_MAIN = "ppio/pa/claude-sonnet-4-6"
MODEL_EXPERT = "ppio/pa/claude-sonnet-4-6"

MAX_ANALYSIS_ROUNDS = 5
MAX_DEBATE_ROUNDS = 3
ANOMALY_THRESHOLD_SIGMA = 2.0
FORECAST_DAYS_DEFAULT = 7
EVENT_CORRELATE_WINDOW_DAYS = 3

EVENTS_FILE = PROJECT_ROOT / "config" / "events.json"
