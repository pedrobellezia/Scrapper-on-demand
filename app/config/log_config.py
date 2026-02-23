import logging
import logging.config
from pathlib import Path
from datetime import datetime
import json
import traceback
import yaml
from rich.logging import RichHandler
from rich.traceback import install as install_traceback

Path("logs").mkdir(exist_ok=True)
install_traceback()


class RichHandlerWrapper(RichHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class JsonlHandler(logging.Handler):
    def __init__(self, log_dir="logs", **kwargs):
        super().__init__(level=logging.WARNING)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def emit(self, record):
        extra = getattr(record, "extra", None)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            **(extra if isinstance(extra, dict) else {}),
            "message": record.message,
        }

        if record.exc_info:
            log_entry["exception"] = "".join(
                traceback.format_exception(*record.exc_info)
            )
        with open(
            self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl",
            "a",
            encoding="utf-8",
        ) as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def setup_logging():
    config_path = Path(__file__).parent / "log.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logging.config.dictConfig(config)
