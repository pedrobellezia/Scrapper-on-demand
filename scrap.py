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
import requests
import os
import asyncio
from playwright.async_api import async_playwright, expect
import base64
from typing import Optional



class Scrap:
    def __init__(self, browser=None, browser_session=None, **launch_options):
        """
        Inicializa a instância do Scrap com as opções de lançamento do navegador.

        Args:
            browser: Instância de browser já criada (opcional).
            browser_session: Caminho para o JSON de sessão.
            **launch_options: Opções para o navegador Playwright (usado apenas se browser não for fornecido).
        """
        self.external_browser = browser
        self.launch_options = launch_options
        self.browser_session = browser_session
        self.ref: dict = {}
        self.files_saved: list = []
        self.iter_args: dict = {}
        self.playwright = None
        self.browser = None

    async def start(self):
        """
        Inicializa o context e a page.
        Se um browser externo for fornecido, usa ele. Caso contrário, cria um novo.
        """
        if self.external_browser:
            # Usa o browser fornecido (global)
            self.browser = self.external_browser
        else:
            # Cria um novo browser (para compatibilidade)
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(**self.launch_options)

        if self.browser_session:
            self.context = await self.browser.new_context(storage_state=self.browser_session)
        else:
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
                if kwargs.get("ignore_error"):
                    return None
                else :
                    error_response = {
                        "erro": str(e),
                        "func": func.__name__,
                        "params": kwargs
                    }

                    print("começando loggin")
                    logging.error(f'Error_response: {error_response}')
                    print("terminando loggin")

                    error_type = type(e).__name__

                    return {
                        "status_code": 500,
                        "message": error_type,
                        "details":{
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
    async def confirm_popup(self, choice: str, value: Optional[str] = None,**kwargs):
        async def handleDialog(dialog):
            match choice:
                case "accept":
                    return await dialog.accept(value)
                case "dismiss":
                    return await dialog.dismiss()
        self.page.on("dialog", handleDialog)
        
    @scrap_wrapper
    async def backspace(self, times: int, **kwargs):
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
    async def go_to(self, url: str, **kwargs):
        """
        Navega até a URL especificada.

        Args:
            url (str): URL de destino.
        """
        await self.page.goto(url)

    @staticmethod
    async def wait(seconds: float, **kwargs):
        """
        Aguarda o tempo passado em segundos.

        Args:
            seconds (float): Tempo de espera em segundos.
        """
        await asyncio.sleep(seconds)

    @scrap_wrapper
    async def read_attribute(self, xpath: str, attribute: str, name: str, **kwargs):
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
    async def read_inner_text(self, name: str, xpath: str = None, **kwargs):
        """
        Lê o texto interno de um elemento HTML e salva em uma variável.

        Args:
            name (str): Nome da variável para salvar o texto.
            xpath (str, optional): XPath do elemento.
        """
        text = await self.page.locator(xpath).inner_text()
        self.ref[name] = text

    @scrap_wrapper
    async def insert(self, xpath: str, text: str, **kwargs):
        """
        Preenche um campo de texto localizado por XPath.

        Args:
            xpath (str): XPath do campo de texto.
            text (str): Texto a ser inserido.
        """
        if kwargs.get("iframe"):
            await self.page.frame_locator(kwargs.get("iframe")).locator(xpath).fill(text)
        else:
            await self.page.locator(xpath).fill(text)

    @scrap_wrapper
    async def click(self, xpath: str, **kwargs):
        """
        Clica em um elemento da página localizado por XPath.

        Args:
            xpath (str): XPath do elemento.
        """
        if kwargs.get("iframe"):
            await self.page.frame_locator(kwargs.get("iframe")).locator(xpath).click()
        else:        
            await self.page.locator(xpath).click()

    @scrap_wrapper
    async def select_option(self, xpath: str, options_list: list, **kwargs):
        """
        Seleciona uma ou mais opções de um <select> usando label ou value.

        Args:
            xpath (str): XPath do elemento select.
            options_list (list): Lista de valores/labels a selecionar.
        """
        await self.page.locator(xpath).select_option(options_list)

    @scrap_wrapper
    async def select(self, xpath: str, **kwargs):
        """
        Verifica a existência de um elemento específico.

        Args:
            xpath (str): XPath do elemento.
        Returns:
            dict | None: Dicionário de erro se não encontrado, None caso contrário.
        """        
        if kwargs.get("iframe"):            
            locator = self.page.frame_locator(kwargs.get("iframe")).locator(xpath)
        else:
            locator = self.page.locator(xpath)
        if await locator.count() == 0:
            return {
                "status_code": 404,
                "message": "Elemento não encontrado",
                "details": {
                    "func": "select",
                    "xpath": xpath,
                    "url": self.page.url,
                }
            }

    @scrap_wrapper
    async def save_file(self, xpath: str, path: str, **kwargs):
        """
        Clica em um elemento que dispara download e salva o arquivo em um diretório.

        Args:
            xpath (str): XPath do botão/link de download.
            path (str): Caminho do diretório para salvar o arquivo.
        """
        os.makedirs(path, exist_ok=True)

        async with self.page.expect_download() as download_info:
            await self.click(xpath, **kwargs)

        file = await download_info.value

        _, ext = os.path.splitext(file.suggested_filename)
        file_name = os.urandom(16).hex() + ext

        full_path = os.path.join(path, file_name)
        await file.save_as(full_path)

        self.files_saved.append({'path': str(file_name)})

    @scrap_wrapper
    async def page_to_pdf(self, path: str, **kwargs):
        """
        Imprime a página atual em PDF e salva no caminho passado.

        Args:
            path (str): Caminho do diretório para salvar o PDF.
        """
        name = os.urandom(16).hex() + ".pdf"
        path = os.path.join(path, name)
        await self.page.pdf(path=path, format="A4")
        self.files_saved.append({'path': str(name)})    

    async def _img_to_base64(self, xpath: str):
        """
        Converte uma imagem localizada por XPath em base64.

        Args:
            xpath (str): XPath da imagem.
        Returns:
            str: Imagem codificada em base64.
        """
        for _ in range(3):
            img_src = await self.page.locator(xpath).get_attribute("src")
            if img_src is None:
                await asyncio.sleep(1)
                continue
            else:
                break
        else:
            raise Exception("Imagem não encontrada no XPath fornecido.")            
                
        if img_src.startswith("data:image"):
            img_src = img_src.split("base64,")[-1].strip()
        else:
            if not img_src.startswith(("http://", "https://")):
                from urllib.parse import urljoin
                page_url = self.page.url
                img_src = urljoin(page_url, img_src)
            
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
    async def switch_page(self, xpath: str, **kwargs):
        """
        Clica em um elemento que abre nova página/aba e troca o contexto para ela.

        Args:
            xpath (str): XPath do elemento.
        """
        async with self.context.expect_page() as new_page_info:
            await self.click(xpath)

        self.page = await new_page_info.value
        await self.page.wait_for_load_state()

    @scrap_wrapper
    async def execute_script(self, script: str, **kwargs):
        """
        Executa um script JavaScript na página atual.

        Args:
            script (str): Código JavaScript a ser executado.
        """
        await self.page.evaluate(script)

    @scrap_wrapper
    async def captcha_solver(self, api_key: str, img_xpath: str = None, input_xpath: str = None, **kwargs):
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
            await self.page.locator("//textarea[@id='g-recaptcha-response']").evaluate(
                "(el) => el.style.display = 'none'"
            )
        else:
            img64 = await self._img_to_base64(img_xpath)
            result = solver.normal(img64, caseSensitive=1)['code']
            await self.page.locator(input_xpath).fill(result)

    @scrap_wrapper
    async def request_pdf(self, path: str, url: str = '', **kwargs):
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
            return {
                "status_code": response.status,
                "message": f"Falha ao baixar PDF: {response.status}"
            }

    @scrap_wrapper
    async def wait_url_change(self, timeout: int, **kwargs):
        """
        Aguarda a mudança da URL atual.

        Args:
            timeout (int): Tempo máximo de espera em milissegundos.
        """
        old_url = self.page.url
        await expect(self.page).not_to_have_url(old_url, timeout=timeout)

    async def close(self):
        """
        Encerra o contexto e a page.
        Só fecha o browser e playwright se foram criados internamente.
        """
        await self.context.close()
        
        # Só fecha o browser se ele foi criado internamente (não é externo)
        if not self.external_browser and self.browser:
            await self.browser.close()
        
        # Só para o playwright se foi iniciado internamente
        if self.playwright:
            await self.playwright.stop()
