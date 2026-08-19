# 联考水表机服务端

*Last Update：2026-08-18*

> 在 GNU General Public License, version 3 or later 之下发布，不提供任何担保。完整声明和条款请见 LICENSE 和 COPYING 文件。

需要与客户端 [juan-ng-client](https://github.com/Waxed-Oxidized-Cut-Copper-Stairs/juan-ng-client) 配套使用。

服务端默认占用系统 6969 端口，可以在 `config/config.conf` 中修改，详见后文配置项目说明。

除非特殊需要且完全了解潜在风险，**不要把服务器暴露到公网！**

**本插件与洛谷、CodeForces 和 AtCoder 官方无任何关联。**

**任何因用户修改或滥用所造成的损害，原作者概不负责。**

## 技术简介

本服务是一个轻量级 **HTTP 代理网关**，为联考水表机客户端提供数据拉取能力。它能把客户端的请求通过浏览器导航转发至目标网站，并将响应原样返回。

网关使用 FastAPI + Uvicorn 搭建，浏览器控制使用 Playwright 实现。

向目标网站发送请求时，会清除 Cookies 并完全重新构造请求头，以保证数据不泄漏。请求时会拦截除主文档以外的任何资源的加载，并禁用 JS。

服务器通过域名白名单校验等方式抵御 SSRF 攻击。

## 部署指南

开发环境参考：

- 操作系统
  - Ubuntu 20.04.6 LTS
- 服务端（代理服务器）环境
  - Python 3.8.10 (3.8.10-0ubuntu1~20.04.18)
  - Playwright 1.48.0
  - FastAPI 0.124.4
  - Uvicorn 0.33.0
  - 详见 requirements.txt
- 无头浏览器
  - Google Chrome 151.0.7922.137

尽管服务端保留对 Python 3.8 的支持，但推荐使用更新版本的 Python。在 Ubuntu 20 下，也可以通过 pyenv 等方式安装高版本 Python。

本程序在 Python 3.14.3 (pyenv 2.6.31-5-g70f096a9) 下通过测试。

接下来介绍如何在 Windows 或 Debian/Ubuntu 上安装。

一、安装 Python 和 Git。

你可以从下面的网页了解如何安装 Python 和 Git。

如果你使用 Debian/Ubuntu，也可以从 APT 安装。

<https://www.python.org/downloads/>

<https://git-scm.com/install/>

二、克隆代码

以下代码将克隆最新版本的服务端，不含 Git 提交历史。

```bash
git clone --depth 1 https://github.com/Waxed-Oxidized-Cut-Copper-Stairs/juan-ng-server.git
cd juan-ng-server
```

三、准备数据文件

你可以将 `example` 目录的内容复制到 `config` 目录下。现在你的目录结构应该类似下图。

```
juan-ng-server/
├── config/
│   ├── config.conf
│   └── data.json
├── example/
│   ├── config.conf
│   └── data.json
├── ...
└── proxy.py
```

`config/data.json` 中存放爬取的目标。目标是分组存放的，**必须填写洛谷 UID，且保证同一个 UID 只出现一次**。

`config/config.conf` 中存放服务端运行的配置项。详见后文的配置项目说明。

四、创建 Python 虚拟环境

虚拟环境可以保护安装的 Python 包不被系统包污染。这一步不是必须的，但推荐这样做。

- 对于 Debian/Ubuntu 用户
  ```bash
  sudo apt install python3-venv
  python3 -m venv .venv
  source .venv/bin/activate  # 激活环境
  ```
- 对于 Windows 用户
  ```powershell
  py -m venv .venv
  .venv\Scripts\activate  # 激活环境
  ```

如果你创建了虚拟环境，请记得在执行后续命令前激活环境。

五、安装 Python 依赖

```bash
pip3 install -r requirements.txt
```

如果网络状况不佳，也可以尝试从镜像站下载。

```bash
pip3 install -r requirements.txt \
  -i https://mirror.tuna.tsinghua.edu.cn/pypi/web/simple
```

六、安装无头浏览器

**方案 A**：使用 Playwright 编译的浏览器（推荐）

```bash
playwright install chrome  # 或 firefox / msedge / chromium
```

编辑 `config/config.conf`，把 `channel` 设置为你选择安装的浏览器。

如果你选择安装 Firefox，还需要把 `browser` 设置为 `firefox`。

**方案 B**：使用系统已安装的浏览器（仅 Chromium 内核）

编辑 `config/config.conf`，把 `executable` 指向系统已安装的浏览器可执行文件路径。

**注意**：若同时指定 `channel` 和 `executable`，优先使用 `executable`。请确保至少指定了二者之一，且正确安装了对应浏览器。

七、启动服务器

- 对于 Debian/Ubuntu 用户
  ```bash
  python3 proxy.py
  ```
- 对于 Windows 用户
  ```bash
  py proxy.py
  ```

你可以用 Ctrl+C 关闭服务器。

八、测试

执行如下命令应该输出 `config/data.json` 的内容。

```bash
curl http://127.0.0.1:6969/data
```

执行如下命令应该输出洛谷 P1001 题目页面的 HTML。

```bash
curl http://127.0.0.1:6969/proxy -H "X-Target-URL: https://www.luogu.com.cn/problem/P1001"
```

如果你修改了 IP 或端口，请在上述命令中使用你修改后的 IP 和端口。

九、增强匿名性

你可以配置二次代理来使用 VPN 发送你的请求。

请在你使用的 VPN 软件中查看其监听的 socks5 端口。以 Clash Verge 为例，点击“订阅”页签右上角的“查看运行时订阅”，记下弹出的配置中 `socks-port` 项目的值。后续演示假设这个值为 `7891`，请在操作时把它替换为实际的端口号。

在 VPN 软件中新建一个 Merge 类型的配置文件，写入如下内容。

```
prepend-rules:
  - IN-PORT,7891,🔰 选择节点
```

请把 `🔰 选择节点` 替换为你的 VPN 服务商实际的节点组。

然后启用配置文件。这个配置的效果是让所有从 `7891` 端口进入代理的流量，忽略 VPN 服务商配置的规则，直接走你选择的 VPN 代理节点。

接下来修改 `config/config.conf` 的 `proxy` 字段，把值设置为如下内容。保存后重启服务器。

```
proxy = socks5://127.0.0.1:7891
```

**注意**：如果你没有启用系统代理或 TUN 模式，但保持 VPN 软件开启，或者 VPN 软件设置为直连，请求仍然会直连。

**注意**：如果你关闭了 VPN 软件，所有请求都会失败。

十、开机自动启动（仅 Linux）

对于 Debian/Ubuntu 用户，可以注册一个用户级 systemd 服务。

创建服务文件。

```bash
mkdir -p ~/.config/systemd/user
vim ~/.config/systemd/user/juan-ng.service
```

并写入如下内容。其中 `%h` 代表用户目录，即 `/home/username`。请把 `%h/path/to/juan-ng-server` 替换成实际安装目录。

```
[Unit]
Description=Juan-NG Server
After=network.target

[Service]
WorkingDirectory=%h/path/to/juan-ng-server
ExecStart=%h/path/to/juan-ng-server/.venv/bin/python3 %h/path/to/juan-ng-server/proxy.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

可以使用如下命令管理服务。

```bash
# 重新加载用户服务配置
systemctl --user daemon-reload

# 启动/停止服务
systemctl --user start juan-ng.service
systemctl --user stop juan-ng.service

# 查看服务状态
systemctl --user status juan-ng.service

# 开启/关闭用户登录时自动启动
systemctl --user enable juan-ng.service
systemctl --user disable juan-ng.service

# 查看日志
journalctl --user -u juan-ng.service -e
```

用户注销时，服务会被自动杀死。

## 配置项目说明

修改配置项需要重启服务器生效。

一、server 章节

- `host` 服务器监听的 IP 地址。默认为 `127.0.0.1`。除非特殊需要且完全了解潜在风险，请不要修改这一项的值。
- `port` 服务器监听的端口。默认为 `6969`。如果修改端口，请记得修改客户端源代码并重新编译客户端。
- `debug` 调试模式开关。

二、playwright 章节

- `browser` 浏览器内核种类。默认为 `chromium`。如果希望使用 Firefox，请改成 `firefox`。
- `channel` 浏览器平台。默认为 `chromium`。可以改成 `chrome` `msedge` `firefox` 等值，请保持与实际安装的浏览器一致。如果指定了 `executable`，此项可以注释掉。
- `executable` 浏览器可执行文件路径。默认被注释掉。可以指定为 Chromium 内核浏览器的可执行文件路径，如 `/usr/bin/google-chrome-stable`。如果指定了 `channel`，此项可以注释掉。此项会覆盖 `channel` 的设置。

三、proxy 章节

- `proxy` 代理 URL。详见部署指南第九部分，增强匿名性。

四、rate 章节

- `ms_per_req` 两次请求间至少间隔的时间。单位为毫秒。默认为 `10000`，即 10 秒。请求频率过快会触发服务端返回 429。
