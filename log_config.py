import logging
import logging.config
from pathlib import Path
from datetime import datetime
import json
import traceback
from rich.logging import RichHandler
from rich.traceback import install as install_traceback

# Diretório de logs
Path("logs").mkdir(exist_ok=True)

# Rich traceback
install_traceback(show_locals=True)

# Handler JSON Lines para warnings e acima
class JsonlHandler(logging.Handler):
    def __init__(self, log_dir="logs"):
        super().__init__(level=logging.WARNING)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def emit(self, record):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = "".join(traceback.format_exception(*record.exc_info))
        with open(self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

# Handler para erros
class ErrorFileHandler(logging.FileHandler):
    def __init__(self, filename="logs/errors.log"):
        super().__init__(filename, mode="a", encoding="utf-8")
        self.setLevel(logging.ERROR)

    def emit(self, record):
        try:
            msg = self.format(record)
            if record.exc_info:
                msg += "\n" + "".join(traceback.format_exception(*record.exc_info))
            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Configuração logging
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        RichHandler(show_time=True, rich_tracebacks=True, tracebacks_show_locals=True),
        JsonlHandler(),
        ErrorFileHandler(),
    ],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)