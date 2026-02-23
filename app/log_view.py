import os
import json
from pathlib import Path
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
import secrets

security = HTTPBasic()
templates = Jinja2Templates(directory="templates")


def verify_credentials(credentials: HTTPBasicCredentials):
    correct_username = os.getenv("DEBUG_USERNAME")
    correct_password = os.getenv("DEBUG_PASSWORD")
    
    if not correct_username or not correct_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credenciais não configuradas no servidor",
        )
    
    is_correct_username = secrets.compare_digest(
        credentials.username, correct_username
    )

    is_correct_password = secrets.compare_digest(
        credentials.password, correct_password)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def read_all_logs():
    logs_dir = Path("logs")
    all_logs = []

    if not logs_dir.exists():
        return all_logs

    jsonl_files = sorted(logs_dir.glob("*.jsonl"), reverse=True)

    for file_path in jsonl_files:
        with open(file_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                try:
                    log_entry = json.loads(line)
                    log_entry["_source_file"] = file_path.name
                    all_logs.append(log_entry)
                except Exception as e:
                    all_logs.append({
                        "error": f"Linha inválida {idx}: {str(e)}",
                        "raw": line.strip(),
                        "_source_file": file_path.name
                    })

    return all_logs


def prepare_log_data(log: dict) -> dict:
    level = log.get('level', 'None')
    timestamp = log.get('timestamp', 'None')
    message = log.get('message', 'None')
    source_file = log.get('_source_file', 'None')
    
    details = {k: v for k, v in log.items() 
              if k not in ['level', 'timestamp', 'message', '_source_file', 'logger']}
    
    details_json = None
    if details:
        details_json = json.dumps(details, indent=2, ensure_ascii=False)
    
    return {
        'level': level,
        'timestamp': timestamp,
        'message': message,
        '_source_file': source_file,
        'details': details if details else None,
        'details_json': details_json
    }


async def debug_logs_view(
    request: Request,
    credentials: HTTPBasicCredentials
):
    verify_credentials(credentials)
    logs = read_all_logs()
    
    prepared_logs = [prepare_log_data(log) for log in logs]

    return templates.TemplateResponse(
        "debug_logs.html",
        {
            "request": request,
            "logs": prepared_logs
        }
    )
