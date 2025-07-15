"""
scrap.py

Módulo para automação de tarefas web utilizando Playwright e 2Captcha.
Inclui funcionalidades para navegação, manipulação de elementos, download de arquivos,
resolução de CAPTCHAs, logging de erros, execução em batch e mais.

"""
from twocaptcha import TwoCaptcha
import logging
import re
from copy import deepcopy
import traceback
import requests
import os
import asyncio
from playwright.async_api import async_playwright, expect
import base64
from datetime import datetime
import json

os.makedirs("logs", exist_ok=True)
timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
log_filename = f"logs/{timestamp}.log"

logging.basicConfig(
    filename=log_filename,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.ERROR
)



class Scrap:
    def __init__(self, **launch_options):
        """
        Inicializa a instância do Scrap com as opções de lançamento do navegador.

        Args:
            **launch_options: Opções para o navegador Playwright.
        """
        self.launch_options = launch_options
        self.ref: dict = {}
        self.files_saved: list = []
        self.iter_args: dict = {}

    async def start(self):
        """
        Inicializa o Playwright, o navegador e a página.
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(**self.launch_options)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    @staticmethod
    def scrap_wrapper(func):
        """
        Decorador para tratamento de erros e controle de execução dos métodos Scrap.

        Args:
            func (Callable): Função a ser decorada.
        Returns:
            Callable: Função decorada.
        """
        async def wrapper(self, *args, **kwargs):
            try:
                if not kwargs.get("ignore_execution"):
                    result = await func(self, *args, **kwargs)
                    return result if result else None
            except Exception as e:
                error_response = {
                    "erro": str(e),
                    "traceback": traceback.format_exc().splitlines(),
                    "func": func.__name__,
                    "params": kwargs
                }
                logging.error(f'Error_response:\n\n{json.dumps(error_response, indent=4, ensure_ascii=False)}')
                return None if kwargs.get("ignore_error") else {
                    "Code": 500,
                    "error_type": type(e).__name__,
                    "last_function":{
                        "name": func.__name__,
                        "args": kwargs,
                    }
                }
        return wrapper

    async def _mekanism(self, data, iteration: int):
        """
        Substitui variáveis do tipo %var/ e {%var/} por seus valores atuais na iteração.

        Args:
            data (Any): Estrutura de dados a ser processada.
            iteration (int): Índice da iteração atual.
        Returns:
            Any: Estrutura de dados com variáveis substituídas.
        """
        if isinstance(data, dict):
            return {k: await self._mekanism(v, iteration) for k, v in data.items()}
        if isinstance(data, list):
            return [await self._mekanism(i, iteration) for i in data]
        if isinstance(data, str):
            if data.startswith("%var/"):
                return self.iter_args.get(data[5:])[iteration]
            elif "{%var/" in data:
                match = re.search(r"\{\s*%var/[^}]+\s*\}", data)
                if match:
                    var_name = match.group(0)[1:-1].strip()
                    var_value = self.iter_args.get(var_name[5:])[iteration]
                    data = re.sub(r"\{\s*%var/[^}]+\s*\}", str(var_value), data)
        return data

    async def batch_mode(self, methods: dict, **kwargs):
        """
        Executa métodos em batch, iterando sobre listas de variáveis fornecidas.

        Args:
            methods (dict): Lista de métodos a serem executados em cada iteração.
            **kwargs: Variáveis iteráveis para cada iteração.
        Returns:
            Any: Resultado do primeiro método que retornar valor não nulo.
        """
        self.iter_args = deepcopy(kwargs)
        for i in range(len(list(iter(kwargs.values()))[0])):
            for items in methods:
                args = deepcopy(items["args"])
                args = await self._mekanism(args, i)
                metodo = getattr(self, items["func"])
                resultado = await metodo(**args)
                if resultado:
                    return resultado

    @scrap_wrapper
    async def confirm_popup(self, timeout: int, **wrapperkwargs):
        """
        Aceita automaticamente popups de confirmação durante o tempo passado.

        Args:
            timeout (int): Tempo total em milissegundos para escutar popups.
        """
        async def _confirm_loop():
            end_time = asyncio.get_event_loop().time() + timeout
            while asyncio.get_event_loop().time() < end_time:
                try:
                    async with self.page.expect_event("dialog", timeout=1000) as dialog_info:
                        dialog = await dialog_info.value
                        await dialog.accept()
                except Exception:
                    await asyncio.sleep(0.1)
        asyncio.create_task(_confirm_loop())

    @scrap_wrapper
    async def backspace(self, times: int, **wrapperkwargs):
        """
        Pressiona a tecla Backspace repetidamente.

        Args:
            times (int): Quantidade de vezes que a tecla será pressionada.
        """
        for _ in range(times):
            await self.page.keyboard.press("Backspace")

    @scrap_wrapper
    async def create_variables(self, **data: dict):
        """
        Cria variáveis internas a partir de pares chave/valor fornecidos.

        Args:
            **data: Pares nome/valor das variáveis a serem criadas.
        """
        for key, value in data.items():
            self.ref[key] = value

    @scrap_wrapper
    async def go_to(self, url: str, **wrapperkwargs):
        """
        Navega até a URL especificada.

        Args:
            url (str): URL de destino.
        """
        await self.page.goto(url)

    @staticmethod
    async def wait(seconds: float, **wrapperkwargs):
        """
        Aguarda o tempo passado em segundos.

        Args:
            seconds (float): Tempo de espera em segundos.
        """
        await asyncio.sleep(seconds)

    @scrap_wrapper
    async def read_attribute(self, xpath: str, attribute: str, name: str, **wrapperkwargs):
        """
        Lê o valor de um atributo HTML e salva em uma variável nomeada.

        Args:
            xpath (str): XPath do elemento.
            attribute (str): Nome do atributo.
            name (str): Nome da variável para salvar o valor.
        """
        attr_value = await self.page.locator(xpath).get_attribute(attribute)
        if attr_value.startswith("data:image/png;base64, "):
            attr_value = attr_value.split("data:image/png;base64, ")[1]
        self.ref[name] =  attr_value

    @scrap_wrapper
    async def read_inner_text(self, name: str, xpath: str = None, **wrapperkwargs):
        """
        Lê o texto interno de um elemento HTML e salva em uma variável.

        Args:
            name (str): Nome da variável para salvar o texto.
            xpath (str, optional): XPath do elemento.
        """
        text = await self.page.locator(xpath).inner_text()
        self.ref[name] = text

    @scrap_wrapper
    async def insert(self, xpath: str, text: str, **wrapperkwargs):
        """
        Preenche um campo de texto localizado por XPath.

        Args:
            xpath (str): XPath do campo de texto.
            text (str): Texto a ser inserido.
        """
        await self.page.locator(xpath).fill(text)

    @scrap_wrapper
    async def click(self, xpath: str, **wrapperkwargs):
        """
        Clica em um elemento da página localizado por XPath.

        Args:
            xpath (str): XPath do elemento.
        """
        await self.page.locator(xpath).click()

    @scrap_wrapper
    async def select_option(self, xpath: str, options_list: list, **wrapperkwargs):
        """
        Seleciona uma ou mais opções de um <select> usando label ou value.

        Args:
            xpath (str): XPath do elemento select.
            options_list (list): Lista de valores/labels a selecionar.
        """
        await self.page.locator(xpath).select_option(options_list)

    @scrap_wrapper
    async def select(self, xpath: str, **wrapperkwargs):
        """
        Verifica a existência de um elemento específico.

        Args:
            xpath (str): XPath do elemento.
        Returns:
            dict | None: Dicionário de erro se não encontrado, None caso contrário.
        """
        if await self.page.locator(xpath).count() == 0:
            return{
                "erro": "Elemento não encontrado",
                "func": "select",
                "xpath": xpath,
                "url": self.page.url,
            }

    @scrap_wrapper
    async def save_file(self, xpath: str, path: str, **wrapperkwargs):
        """
        Clica em um elemento que dispara download e salva o arquivo em um diretório.

        Args:
            xpath (str): XPath do botão/link de download.
            path (str): Caminho do diretório para salvar o arquivo.
        """
        os.makedirs(path, exist_ok=True)

        async with self.page.expect_download() as download_info:
            await self.page.locator(xpath).click()

        file = await download_info.value

        _, ext = os.path.splitext(file.suggested_filename)
        file_name = os.urandom(16).hex() + ext

        full_path = os.path.join(path, file_name)
        await file.save_as(full_path)

        self.files_saved.append({'path': str(full_path)})

    @scrap_wrapper
    async def page_to_pdf(self, path: str, **wrapperkwargs):
        """
        Imprime a página atual em PDF e salva no caminho passado.

        Args:
            path (str): Caminho do diretório para salvar o PDF.
        """
        name = os.urandom(16).hex() + ".pdf"
        path = os.path.join(path, name)
        await self.page.pdf(path=path, format="A4")

    @scrap_wrapper
    async def set_timeout(self, timeout: int, **wrapperkwargs):
        """
        Define o timeout padrão para todas as ações.

        Args:
            timeout (int): Tempo de timeout em milissegundos.
        """
        self.page.set_default_timeout(timeout)
        self.context.set_default_timeout(timeout)

    async def _img_to_base64(self, xpath: str):
        """
        Converte uma imagem localizada por XPath em base64.

        Args:
            xpath (str): XPath da imagem.
        Returns:
            str: Imagem codificada em base64.
        """
        img_src = await self.page.locator(xpath).get_attribute("src")
        if img_src.startswith("data:image"):
            img_src = img_src.split("base64,")[-1].strip()
        else:
            img_bytes = requests.get(img_src).content
            img_src = base64.b64encode(img_bytes).decode('utf-8')
        return img_src

    async def _replace_text(self, text: str):
        """
        Substitui $ref/variavel pelo valor salvo em self.ref.

        Args:
            text (str): Texto a ser processado.
        Returns:
            str: Texto com variáveis substituídas.
        """
        if text.startswith("$ref/"):
            return self.ref[text.split("$ref/")[1]]
        return text

    @scrap_wrapper
    async def switch_page(self, xpath: str, **wrapperkwargs):
        """
        Clica em um elemento que abre nova página/aba e troca o contexto para ela.

        Args:
            xpath (str): XPath do elemento.
        """
        async with self.context.expect_page() as new_page_info:
            await self.page.locator(xpath).click()

        self.page = await new_page_info.value
        await self.page.wait_for_load_state()

    @scrap_wrapper
    async def execute_script(self, script: str, **wrapperkwargs):
        """
        Executa um script JavaScript na página atual.

        Args:
            script (str): Código JavaScript a ser executado.
        """
        await self.page.evaluate(script)

    @scrap_wrapper
    async def captcha_solver(self, api_key: str, img_xpath: str = None, input_xpath: str = None, **wrapperkwargs):
        """
        Resolve CAPTCHA usando a API 2Captcha. Suporta modo automático e manual.

        Args:
            api_key (str): Chave da API 2Captcha.
            img_xpath (str, optional): XPath da imagem do CAPTCHA (modo manual).
            input_xpath (str, optional): XPath do campo de input (modo manual).
        """
        solver = TwoCaptcha(api_key)
        if not img_xpath:
            src = await self.page.locator("//iframe[@title = 'reCAPTCHA']").first.get_attribute("src")
            sitekey = src.split("k=")[1].split("&")[0]
            url = self.page.url
            result = solver.recaptcha(sitekey=sitekey, url=url)
            token = result['code']
            await self.page.locator("//textarea[@id='g-recaptcha-response']").evaluate(
                "(el) => el.style.display = 'block'"
            )
            await self.page.locator("//textarea[@id='g-recaptcha-response']").fill(token)
        else:
            img64 = await self._img_to_base64(img_xpath)
            result = solver.normal(img64, caseSensitive=1)['code']
            await self.page.locator(input_xpath).fill(result)

    @scrap_wrapper
    async def request_pdf(self, path: str, url: str = '', **wrapperkwargs):
        """
        Baixa a página como PDF caso a URL aponte para um PDF. Se não informado, usa a URL atual.

        Args:
            path (str): Caminho do diretório para salvar o PDF.
            url (str, optional): URL do PDF. Se não informado, usa a URL atual.
        Returns:
            dict | None: Dicionário de erro se falhar, None se sucesso.
        """
        if not url:
            url = self.page.url
        response = await self.page.context.request.get(url)
        if response.ok:
            file_path = f"{path}/{os.urandom(16).hex()}.pdf"
            with open(file_path, "wb") as f:
                f.write(await response.body())
        else:
            return {"error": f"Falha ao baixar PDF: {response.status}"}

    @scrap_wrapper
    async def wait_url_change(self, timeout: int, **wrapperkwargs):
        """
        Aguarda a mudança da URL atual.

        Args:
            timeout (int): Tempo máximo de espera em milissegundos.
        """
        old_url = self.page.url
        await expect(self.page).not_to_have_url(old_url, timeout=timeout)

    async def close(self):
        """
        Encerra o contexto, o navegador e o Playwright.
        """
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()
