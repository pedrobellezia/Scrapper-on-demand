"""
Módulo principal da API.

Este módulo expõe um endpoint FastAPI para executar rotinas de scraping que operam baseadas num JSON,
utilizando a classe Scrap para automação de navegador.
"""

import re
from typing import Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from scrap import Scrap
from datetime import datetime
from data_validation import validate
import pytz
import os
import logging
app = FastAPI()
tz = pytz.timezone("America/Sao_Paulo")

# Montar pasta estática para servir PDFs
app.mount("/pdf", StaticFiles(directory="static/pdf"), name="cnd")

os.makedirs("logs", exist_ok=True)
timestamp = datetime.now().strftime("%d-%m-%Y")
log_filename = f"logs/{timestamp}.log"
logging.basicConfig(
    filename=log_filename,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.ERROR,
    force=True
)

async def change_variables(data: Any , scrapper: Scrap) -> Any:
    """
    Substitui variáveis do tipo $ref/ e {$ref/} por seus valores salvos no scrapper.
    Funciona recursivamente para strings, listas e dicionários.

    Args:
        data (any): Estrutura de dados a ser processada.
        scrapper (Scrap): Instância de Scrap para buscar os valores das variáveis.

    Returns:
        any: Estrutura de dados com as variáveis substituídas por seus valores reais.
    """
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
    """
    Endpoint principal para execução de rotinas de scraping.
    Recebe um JSON com as opções do navegador e a lista de passos a executar.
    Executa cada passo sequencialmente, processando variáveis dinâmicas.

    Args:
        request (Request): Objeto Request do FastAPI contendo o JSON de entrada.

    Returns:
        dict: Resultado do scraping, incluindo variáveis lidas e arquivos salvos.
    """
    data = await request.json()
    success, data = validate(data)
    
    if not success:
        logging.error(f'Error_response: {data}')
        raise HTTPException(status_code=422, detail=data)

    
    scrapper = Scrap(browser_session=data.get("browser_session"), **data["options"])
    await scrapper.start()
    for step in data["steps"]:
        print(f"Metodo: {step['func']}", flush=True)
        print(f"começando em: {datetime.now(tz).strftime('[%d/%m/%y %H:%M:%S]')}", flush=True)  
        metodo = getattr(scrapper, step["func"])
        if "xpath" in step["args"]:
            if not step["args"]["xpath"].startswith("xpath="):
                step["args"]["xpath"] = "xpath=" + step["args"]["xpath"]
        new_steps = await change_variables(step["args"], scrapper)
        resultado = await metodo(**new_steps)
        print(f"terminando em: {datetime.now(tz).strftime('[%d/%m/%y %H:%M:%S]')}", flush=True)  
        if resultado:
            raise HTTPException(status_code=500, detail=resultado)
            
    await scrapper.close()    
    retorno = {
        "message": "Scraping executado com sucesso",
        "atributes_read": scrapper.ref,
        "files_saved": scrapper.files_saved,
    }
    
    return retorno
if __name__ == "__main__":
    """
    Inicializa o servidor FastAPI localmente usando Uvicorn.
    """
    import uvicorn
    print("Starting FastAPI app...")
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=False)
