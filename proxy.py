from asyncio import Lock
from contextlib import asynccontextmanager
from urllib.parse import urlparse, urlunparse
import configparser
import json

from fastapi import FastAPI, Request, Response, HTTPException
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext
import uvicorn

PROXY_HOSTNAME = [
    "www.luogu.com.cn",
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

# 被过滤的响应头
RESPONSE_HEADER_FILTER = {
    "content-encoding", "transfer-encoding", "content-length",
    "set-cookie"
}

with open("config/data.json") as file:
    data = json.load(file)

playwright: Playwright = None
browser: Browser = None
context: BrowserContext = None
@asynccontextmanager
async def lifespan(app: FastAPI):
    global playwright, browser, context
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
    user_agent = await page.evaluate("navigator.userAgent")
    user_agent = user_agent.replace("Headless", "")
    await tmp_context.close()
    context = await browser.new_context(user_agent=user_agent)
    try:
        yield
    finally:
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
    url = urlunparse(url)
    async with lock:
        await context.clear_cookies()
        cnt = 0
        # 手动重定向以避免 SSRF
        try:
            while cnt <= 20:
                resp = await context.request.fetch(
                    url,
                    method=request.method,
                    timeout=10000,
                    max_redirects=0,
                )
                if resp.status not in (301, 302, 303, 307, 308):
                    break
                location = resp.headers.get("location")
                if not location:
                    break
                url = urlparse(location, "https")
                if url.hostname not in PROXY_HOSTNAME or (url.port and url.port != 443):
                    raise HTTPException(403, "Redirect to non-whitelisted host")
                if url.scheme != "https":
                    raise HTTPException(403, "Redirect to non-HTTPS protocol")
                url = urlunparse(url)
                cnt += 1
            else:
                raise HTTPException(502, "Too many redirects")
        except Exception as e:
            print(e)
            raise HTTPException(502)
    resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in RESPONSE_HEADER_FILTER}
    return Response(
        content=await resp.body(),
        status_code=resp.status,
        headers=resp_headers,
    )

if __name__ == "__main__":
    uvicorn.run("proxy:app", host=HOST, port=PORT, reload=DEBUG, log_level="info")
