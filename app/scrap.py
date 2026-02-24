import concurrent.futures
from app.config.state import worker_id
from twocaptcha import TwoCaptcha
import logging
import re
from copy import deepcopy
import os
import asyncio
from playwright.async_api import async_playwright, expect
import base64
from typing import Optional

logger = logging.getLogger(__name__)


class Scrap:
    def __init__(self, browser=None, browser_session=None, **launch_options):
        self.external_browser = browser
        self.launch_options = launch_options
        self.browser_session = browser_session
        self.ref: dict = {}
        self.files_saved: list = []
        self.iter_args: dict = {}
        self.playwright = None
        self.browser = None

    async def start(self):
        if self.external_browser:
            self.browser = self.external_browser
        else:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(**self.launch_options)

        if self.browser_session:
            self.context = await self.browser.new_context(
                storage_state=self.browser_session
            )
        else:
            self.context = await self.browser.new_context()

        self.page = await self.context.new_page()

    @staticmethod
    def scrap_wrapper(func):
        async def wrapper(self, *args, **kwargs):
            tries = deepcopy(kwargs).get("executions", 1)
            for attempt in range(tries):
                try:
                    result = await func(self, *args, **kwargs)
                    return result if result else None
                except Exception as e:
                    if attempt < tries - 1 or kwargs.get("ignore_error"):
                        continue
                    else:
                        extra = {
                            "erro": str(e),
                            "func": func.__name__,
                            "params": kwargs,
                            "worker": worker_id.get(),
                        }

                        file_name = "Não foi possível salvar a página em pdf"

                        try:
                            file_name = f"{worker_id.get()}.pdf"
                            await self.page.pdf(path=f"static/error/{file_name}")
                            extra.update({"file_name": file_name})
                        except Exception as pdf_error:
                            extra.update({"file_name": file_name})
                            logging.debug(pdf_error)

                        logger.error(
                            f"Worker: {worker_id.get()} || Erro na execução do step",
                            extra={"extra": extra},
                        )

                        return {
                            "status_code": 500,
                            "message": type(e).__name__,
                            "details": {
                                "name": func.__name__,
                                "args": kwargs,
                                "screenshot_url": file_name,
                            },
                        }

        return wrapper

    async def _mekanism(self, data, iteration: int):
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

    # async def batch_mode(self, methods: dict, **kwargs):
    #     self.iter_args = deepcopy(kwargs)
    #     for i in range(len(list(iter(kwargs.values()))[0])):
    #         for items in methods:
    #             args = deepcopy(items["args"])
    #             args = await self._mekanism(args, i)
    #             metodo = getattr(self, items["func"])
    #             resultado = await metodo(**args)
    #             if resultado:
    #                 return resultado

    @scrap_wrapper
    async def confirm_popup(self, choice: str, value: Optional[str] = None, **kwargs):
        async def handleDialog(dialog):
            match choice:
                case "accept":
                    return await dialog.accept(value)
                case "dismiss":
                    return await dialog.dismiss()

        self.page.on("dialog", handleDialog)

    @scrap_wrapper
    async def backspace(self, times: int, **kwargs):
        for _ in range(times):
            await self.page.keyboard.press("Backspace")

    @scrap_wrapper
    async def create_variables(self, **data: dict):
        for key, value in data.items():
            self.ref[key] = value

    @scrap_wrapper
    async def go_to(self, url: str, **kwargs):
        await self.page.goto(url)

    @staticmethod
    async def wait(seconds: float, **kwargs):
        await asyncio.sleep(seconds)

    @scrap_wrapper
    async def read_attribute(self, xpath: str, attribute: str, name: str, **kwargs):
        attr_value = await self.page.locator(xpath).get_attribute(attribute)
        if attr_value.startswith("data:image/png;base64, "):
            attr_value = attr_value.split("data:image/png;base64, ")[1]
        self.ref[name] = attr_value

    @scrap_wrapper
    async def read_inner_text(self, name: str, xpath: str = None, **kwargs):
        text = await self.page.locator(xpath).inner_text()
        self.ref[name] = text

    @scrap_wrapper
    async def insert(self, xpath: str, text: str, **kwargs):
        if kwargs.get("iframe"):
            await (
                self.page.frame_locator(kwargs.get("iframe")).locator(xpath).fill(text)
            )
        else:
            await self.page.locator(xpath).fill(text)

    @scrap_wrapper
    async def click(self, xpath: str, **kwargs):
        if kwargs.get("iframe"):
            await self.page.frame_locator(kwargs.get("iframe")).locator(xpath).click()
        else:
            await self.page.locator(xpath).click()

    @scrap_wrapper
    async def select_option(self, xpath: str, options_list: list, **kwargs):
        await self.page.locator(xpath).select_option(options_list)

    @scrap_wrapper
    async def select(self, xpath: str, **kwargs):
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
                },
            }

    @scrap_wrapper
    async def save_file(self, xpath: str, path: str = "static/pdf", **kwargs):
        os.makedirs(path, exist_ok=True)

        async with self.page.expect_download() as download_info:
            await self.click(xpath, **kwargs)

        file = await download_info.value

        _, ext = os.path.splitext(file.suggested_filename)
        file_name = os.urandom(16).hex() + ext

        full_path = os.path.join(path, file_name)
        await file.save_as(full_path)

        self.files_saved.append({"path": str(file_name)})

    @scrap_wrapper
    async def page_to_pdf(self, path: str = "static/pdf", **kwargs):
        os.makedirs(path, exist_ok=True)
        name = os.urandom(16).hex() + ".pdf"
        path = os.path.join(path, name)
        await self.page.pdf(path=path, format="A4")
        self.files_saved.append({"path": str(name)})

    async def _img_to_base64(self, xpath: str):
        for _ in range(3):
            locator = self.page.locator(xpath)
            if await locator.count() == 0:
                await asyncio.sleep(1)
                continue
            else:
                break
        else:
            raise Exception("Imagem não encontrada no XPath fornecido.")

        img_src = await locator.get_attribute("src")

        if img_src and img_src.startswith("data:image"):
            img_src = img_src.split("base64,")[-1].strip()
        else:
            screenshot_bytes = await locator.screenshot()
            img_src = base64.b64encode(screenshot_bytes).decode("utf-8")

        return img_src

    async def _replace_text(self, text: str):
        if text.startswith("$ref/"):
            return self.ref[text.split("$ref/")[1]]
        return text

    @scrap_wrapper
    async def switch_page(self, xpath: str, **kwargs):
        async with self.context.expect_page() as new_page_info:
            await self.click(xpath)

        self.page = await new_page_info.value
        await self.page.wait_for_load_state()

    @scrap_wrapper
    async def execute_script(self, script: str, **kwargs):
        await self.page.evaluate(script)

    @scrap_wrapper
    async def captcha_solver(
        self, api_key: str, img_xpath: str = None, input_xpath: str = None, **kwargs
    ):
        loop = asyncio.get_running_loop()
        solver = TwoCaptcha(api_key)

        with concurrent.futures.ThreadPoolExecutor() as pool:
            if not img_xpath:
                src = await self.page.locator(
                    "//iframe[@title = 'reCAPTCHA']"
                ).first.get_attribute("src")
                sitekey = src.split("k=")[1].split("&")[0]
                url = self.page.url
                result = await loop.run_in_executor(
                    pool, lambda: solver.recaptcha(sitekey=sitekey, url=url)
                )
                token = result["code"]
                await self.page.locator(
                    "//textarea[@id='g-recaptcha-response']"
                ).evaluate("(el) => el.style.display = 'block'")
                await self.page.locator("//textarea[@id='g-recaptcha-response']").fill(
                    token
                )
                await self.page.locator(
                    "//textarea[@id='g-recaptcha-response']"
                ).evaluate("(el) => el.style.display = 'none'")
            else:
                img64 = await self._img_to_base64(img_xpath)
                result = await loop.run_in_executor(
                    pool, lambda: solver.normal(img64, caseSensitive=1)["code"]
                )
                await self.page.locator(input_xpath).fill(result)

    @scrap_wrapper
    async def request_pdf(self, path: str = "static/pdf", url: str = "", **kwargs):
        os.makedirs(path, exist_ok=True)
        if not url:
            url = self.page.url
        response = await self.page.context.request.get(url)
        if response.ok:
            file_name = os.urandom(16).hex() + ".pdf"
            file_path = os.path.join(path, file_name)
            self.files_saved.append({"path": str(file_name)})
            with open(file_path, "wb") as f:
                f.write(await response.body())
        else:
            return {
                "status_code": response.status,
                "message": f"Falha ao baixar PDF: {response.status}",
            }

    @scrap_wrapper
    async def wait_url_change(self, timeout: int, **kwargs):
        old_url = self.page.url
        await expect(self.page).not_to_have_url(old_url, timeout=timeout)

    async def close(self):
        await self.context.close()

        if not self.external_browser and self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()
