import os
import decimal
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# telegram settings
T_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# smt server settings
HOST_EMAIL = os.environ.get("HOST_EMAIL")
HOST_EMIL_PASSWORD = os.environ.get("HOST_EMIL_PASSWORD")


DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PSWD = os.getenv("POSTGRES_PASSWORD", "password")
DB_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB_NAME", "crypto_bot")
PG_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PSWD}@{DB_HOST}/{DB_NAME}"

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
# time when order is expired in min
T_EXPIRE = 1

KUNA_BASE_URL = "https://api.kuna.io:443"
KUNA_VERSION = "/v3"
KUNA_V3_URL = KUNA_BASE_URL + KUNA_VERSION
KUNA_EXCHANGE_RATES = KUNA_V3_URL + "/exchange-rates/"
KUNA_FEES_URL = KUNA_V3_URL + "/fees/"
KUNDA_DEPOSIT_URL = KUNA_V3_URL + "/auth/deposit"
KUNA_TIKETS_URL = KUNA_V3_URL + "/tickers"


KUNA_SECRET_KEY = os.getenv("KUNA_SECRET_KEY", "")
KUNA_PUBLIC_KEY = os.getenv("KUNA_PUBLIC_KEY", "")

MARKUP = decimal.Decimal("0.03")

