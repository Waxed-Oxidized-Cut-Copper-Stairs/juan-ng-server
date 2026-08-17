from asyncio import Lock
from contextlib import asynccontextmanager
from urllib.parse import urlparse, urlunparse
import configparser
import json
import logging

from fastapi import FastAPI, Request, Response, HTTPException
from playwright.async_api import async_playwright, BrowserContext, Route
import uvicorn

logger = logging.getLogger("uvicorn")

PROXY_HOSTNAME = [
    "www.luogu.com.cn",
    "www.luogu.com"
]

config = configparser.ConfigParser()
config.read("config/config.conf")

# 代理服务器配置
HOST = config.get("server", "host")
PORT = config.getint("server", "port")
DEBUG = config.getboolean("server", "debug")

# Playwright 配置
BROWSER = config.get("playwright", "browser")
CHANNEL = config.get("playwright", "channel", fallback=None)
EXECUTABLE_PATH = config.get("playwright", "executable", fallback=None)
if CHANNEL is None and EXECUTABLE_PATH is None:
    raise ValueError("没有指定 Playwright 使用的浏览器")

# 二次代理配置
PROXY = config.get("proxy", "proxy", fallback=None)

# 被过滤的响应头
RESPONSE_HEADER_FILTER = {
    "content-encoding", "transfer-encoding", "content-length",
    "set-cookie"
}

with open("config/data.json") as file:
    data = json.load(file)

context: BrowserContext = None
@asynccontextmanager
async def lifespan(app: FastAPI):
    global context
    playwright = await async_playwright().start()
    browser = await {
        "chromium": playwright.chromium,
        "firefox": playwright.firefox,
        "webkit": playwright.webkit,
    }[BROWSER].launch(
        channel=CHANNEL,
        executable_path=EXECUTABLE_PATH,
        headless=True,
    )
    tmp_context = await browser.new_context()
    page = await tmp_context.new_page()
    user_agent: str = await page.evaluate("navigator.userAgent")
    user_agent = user_agent.replace("Headless", "").strip()
    await tmp_context.close()
    context = await browser.new_context(
        user_agent=user_agent,
        java_script_enabled=False,
        proxy={ "server": PROXY }
    )
    try:
        yield
    finally:
        try:
            await context.close()
        except Exception as e:
            logger.error(e)
        try:
            await browser.close()
        except Exception as e:
            logger.error(e)
        await playwright.stop()

app = FastAPI(lifespan=lifespan)

@app.api_route("/data", methods=["GET"])
async def route_data():
    return data

lock = Lock()

@app.api_route("/proxy", methods=["GET"])
async def route_proxy(request: Request):
    url = request.headers.get("x-target-url")
    if not url:
        raise HTTPException(400, "Missing X-Target-URL header")
    url = urlparse(url, "https")
    if url.scheme != "https":
        raise HTTPException(400, "X-Target-URL should use HTTPS")
    if url.hostname not in PROXY_HOSTNAME or (url.port and url.port != 443):
        raise HTTPException(400, "X-Target-URL is non-whitelisted")
    # if PROXY is not None and url.hostname == "www.luogu.com.cn":
    #     url = url._replace(netloc="www.luogu.com")
    #     logger.info(f"Use proxy: www.luogu.com.cn -> www.luogu.com")
    url = urlunparse(url)
    logger.info(f"X-Target-URL: {url}")
    async with lock:
        await context.clear_cookies()
        page = await context.new_page()
        cnt = 0
        err = None
        # 使用浏览器导航替代 APIRequestContext
        # 手动重定向以避免 SSRF
        # 拦截资源加载、禁用 JS
        async def route_handler(route: Route):
            nonlocal cnt, err
            req = route.request
            if req.resource_type != "document":
                await route.abort()
                return
            if cnt > 20:
                err = HTTPException(502, "Too many redirects")
                await route.abort()
                return
            url = urlparse(req.url, "https")
            if url.hostname not in PROXY_HOSTNAME or (url.port and url.port != 443):
                err = HTTPException(403, "Redirect to non-whitelisted host")
                await route.abort()
                return
            if url.scheme != "https":
                err = HTTPException(403, "Redirect to non-HTTPS protocol")
                await route.abort()
                return
            url = urlunparse(url)
            if cnt == 0:
                logger.info(f"Navigate to {url}")
            else:
                logger.info(f"Redirect to {url}")
            cnt += 1
            await route.continue_()
        await page.route("**/*", route_handler)
        try:
            resp = await page.goto(url, wait_until="load", timeout=10000)
        except Exception as e:
            print(e)
            if err is not None:
                raise err
            raise HTTPException(502)
        if resp is None:
            raise HTTPException(502, "No response")
    resp_headers = {}
    for k, v in resp.headers.items():
        if k.lower() in RESPONSE_HEADER_FILTER:
            continue
        resp_headers[k] = v.replace("\r", "").replace("\n", "")
    return Response(
        content=await resp.body(),
        status_code=resp.status,
        headers=resp_headers,
    )

if __name__ == "__main__":
    uvicorn.run("proxy:app", host=HOST, port=PORT, reload=DEBUG, log_level="info")
