"""Carrega variáveis de ambiente e expõe constantes globais."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")

def _int(key, default=0):
    v = os.getenv(key, "")
    try:
        return int(v) if v and v.isdigit() else default
    except Exception:
        return default

TOKEN         = os.getenv("DISCORD_TOKEN", "")
CLIENT_ID     = _int("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
GUILD_ID      = _int("DISCORD_GUILD_ID")
OWNER_ID      = _int("OWNER_ID")

BOT_NAME   = os.getenv("BOT_NAME", "Bot de Vendas")
BOT_COLOR  = _int("BOT_COLOR", 5763719)
BOT_FOOTER = os.getenv("BOT_FOOTER", f"(c) {BOT_NAME}")

LOG_CHANNEL_ID      = _int("LOG_CHANNEL_ID")
CONF_CHANNEL_ID     = _int("CONF_CHANNEL_ID")
VERIFY_CHANNEL_ID   = _int("VERIFY_CHANNEL_ID")
CATEGORY_ID         = _int("CATEGORY_ID")
WELCOME_CHANNEL_ID  = _int("WELCOME_CHANNEL_ID")

VERIFIED_ROLE_ID    = _int("VERIFIED_ROLE_ID")
UNVERIFIED_ROLE_ID  = _int("UNVERIFIED_ROLE_ID")
OAUTH_REDIRECT_URI  = os.getenv("OAUTH_REDIRECT_URI", "")

PAYMENT_MODE  = os.getenv("PAYMENT_MODE", "manual").lower()
PIX_CHAVE     = os.getenv("PIX_CHAVE", "")
PIX_NOME      = (os.getenv("PIX_NOME", "TITULAR") or "TITULAR")[:25].upper()
PIX_CIDADE    = (os.getenv("PIX_CIDADE", "BRASIL") or "BRASIL")[:15].upper()
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")

if not TOKEN:
    raise SystemExit("❌ DISCORD_TOKEN ausente no .env")
if not OWNER_ID:
    raise SystemExit("❌ OWNER_ID ausente no .env")
