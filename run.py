"""WallStreet Sentinel — entry point.  python run.py"""
import logging
import socket
import sys
from logging.handlers import RotatingFileHandler

from wsb.config import DATA_DIR, DISCORD_TOKEN


def main() -> None:
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fh = RotatingFileHandler(DATA_DIR / "sentinel.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.addHandler(fh)
    root.addHandler(sh)
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)   # Yahoo failures are summarised by our own warnings

    if not DISCORD_TOKEN:
        sys.exit("❌ 請在 .env 設定 DISCORD_BOT_TOKEN")

    # single-instance guard (prevents duplicate alerts)
    guard = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        guard.bind(("127.0.0.1", 47831))
    except OSError:
        sys.exit("❌ 已有一個 WallStreet Sentinel 在執行")

    # self-heal: install packages added after the first setup (e.g. Pillow for slides)
    import importlib
    import subprocess
    for mod, pkg in (("PIL", "Pillow>=10.0"),):
        try:
            importlib.import_module(mod)
        except ImportError:
            logging.info("installing missing package %s …", pkg)
            subprocess.call([sys.executable, "-m", "pip", "install", "-q", pkg])

    from wsb.bot.app import Sentinel
    Sentinel().run(DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
