# 联考水表机服务端

> 在 GNU General Public License, version 3 or later 之下发布，不提供任何担保。完整声明和条款请见 LICENSE 和 COPYING 文件。

**本插件与洛谷、CodeForces 和 AtCoder 官方无任何关联。**

**任何因用户修改或滥用所造成的损害，原作者概不负责。**

## 环境要求

需要与客户端 [juan-ng-client](https://github.com/Wang-Yile/juan-ng-client) 配套使用。

## 技术简介

服务端使用 Python Playwright + FastAPI 编写，使用无头浏览器转发到特定网站的 HTTP GET 请求。

## 部署指南

开发环境参考：

- 操作系统
  - Ubuntu 20.04.6 LTS
- 服务端（代理服务器）环境
  - Python 3.14.3 (pyenv 2.6.31-5-g70f096a9)
  - Playwright 1.60.0
  - FastAPI 0.137.2
  - Uvicorn 0.49.0
  - Jinja2 3.1.6
- 无头浏览器
  - Google Chrome 151.0.7922.137
