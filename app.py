from playwright.async_api import async_playwright
import re
from typing import Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from scrap import Scrap
from datetime import datetime
from data_validation import validate
import pytz
import logging
from contextlib import asynccontextmanager
import asyncio
import log_config

tz = pytz.timezone("America/Sao_Paulo")
logger = logging.getLogger(__name__)

playwright = None
browser = None
semaphore = None  

@asynccontextmanager
async def lifespan(app: FastAPI):
    global playwright, browser, semaphore
    semaphore = asyncio.Semaphore(3)  
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        args=[
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars"
        ],
        slow_mo=1000,
        headless=False
    )
    yield
    await browser.close()
    await playwright.stop()

app = FastAPI(lifespan=lifespan)

app.mount("/pdf", StaticFiles(directory="static/pdf"), name="cnd")



async def change_variables(data: Any , scrapper: Scrap) -> Any:
    if isinstance(data, str):
        if data.startswith("$ref/"):
            data = await scrapper._replace_text(data)
        elif "{$ref/" in data:
            match = re.search(r"\{\s*\$ref\/[^}]+\s*\}", data)
            if match:
                text = await scrapper._replace_text(match.group(0)[1:-1])
                data = re.sub(r"\{\s*\$ref\/[^}]+\s*\}", text, data)
    elif isinstance(data, list):
        data = [await change_variables(item, scrapper) for item in data]
    elif isinstance(data, dict):
        data = {k: await change_variables(v, scrapper) for k,v in data.items()}
    return data

@app.post("/execute_scrap")
async def execute_scrap(request: Request) -> dict:
    async with semaphore:
        return await _execute_scrap_internal(request)

async def _execute_scrap_internal(request: Request) -> dict:
    data = await request.json()
    success, response = validate(data)

    if not success:
        logger.error(f'Erro de validação: {response}')
        raise HTTPException(status_code=422, detail=response)

    data = response["data"]
    timeout = data.pop("timeout", None)
    logger.debug(f'Timeout configurado: {timeout}')

    scrapper = Scrap(browser=browser, browser_session=data.get("browser_session"))
    await scrapper.start()
    
    if timeout:
        scrapper.page.set_default_timeout(timeout)
        scrapper.context.set_default_timeout(timeout)

    for step in data["steps"]:
        logger.info(f"Executando método: {step['func']}")
        logger.debug(f"Início: {datetime.now(tz).strftime('[%d/%m/%y %H:%M:%S]')}")
        metodo = getattr(scrapper, step["func"])
        if "xpath" in step["args"]:
            if not step["args"]["xpath"].startswith("xpath="):
                step["args"]["xpath"] = "xpath=" + step["args"]["xpath"]
        new_steps = await change_variables(step["args"], scrapper)
        resultado = await metodo(**new_steps)
        logger.debug(f"Fim: {datetime.now(tz).strftime('[%d/%m/%y %H:%M:%S]')}")
        if resultado:
            raise HTTPException(status_code=500, detail=resultado)
            
    await scrapper.close()    
    retorno = {
        "status": "success",
        "message": "Scraping executado com sucesso",
        "data": {
            "atributes_read": scrapper.ref,
            "files_saved": scrapper.files_saved,
        }
    }
    
    return retorno
if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando aplicação FastAPI...")
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=False)
