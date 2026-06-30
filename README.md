<div align="center">

# 🔐 2FA Authenticator

**English** | [中文](#中文)

A secure two-factor authentication (2FA) authenticator app built with Python and Flet, featuring encrypted vault storage and GitHub integration.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/Flet-Flutter%20based-purple.svg)](https://flet.dev)

</div>

---

## ✨ Features

- 🔑 **TOTP/HOTP Support** — Generate and verify time-based and counter-based one-time passwords (RFC 6238 / RFC 4226)
- 🔒 **Encrypted Vault** — All secrets stored with Argon2id key derivation + AES-128-CBC (Fernet) encryption
- 🐙 **GitHub Integration** — OAuth Device Flow, 2FA status check, account management
- 📷 **QR Code Support** — Scan from camera (mobile) or image files, generate QR codes
- 📦 **Import/Export** — Compatible with Google Authenticator, Aegis Authenticator, and generic `otpauth://` URI formats
- 🎨 **Material Design 3** — Modern, clean UI built with Flet (Flutter-based)
- 🔐 **Auto-lock** — Vault locks automatically after configurable inactivity timeout
- 📋 **Clipboard Auto-clear** — Copied codes are cleared after 30 seconds
- 🛡️ **Brute-force Protection** — Lockout after 5 failed password attempts
- ⏰ **NTP Time Sync** — Detects clock drift to ensure accurate OTP generation

## 📱 Supported Platforms

| Platform | Status |
|----------|--------|
| Android  | ✅ Primary target |
| macOS    | ✅ Supported |
| Windows  | ✅ Supported |
| Linux    | ✅ Supported |
| iOS      | 🔧 Experimental |
| Web      | 🔧 Experimental |

## 📸 Screenshots

> Coming soon

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| UI Framework | [Flet](https://flet.dev) (Flutter-based) |
| OTP Core | [pyotp](https://github.com/pyauth/pyotp) |
| Encryption | [cryptography](https://cryptography.io) (Fernet/AES) |
| Key Derivation | [argon2-cffi](https://github.com/hynek/argon2-cffi) |
| Database | SQLite + [SQLModel](https://sqlmodel.tiangolo.com) |
| QR Codes | [qrcode](https://github.com/lincolnloop/python-qrcode) + [pyzbar](https://github.com/NaturalHistoryMuseum/pyzbar) |
| HTTP Client | [httpx](https://github.com/encode/httpx) |
| OAuth | [authlib](https://github.com/lepture/authlib) |

## 🚀 Installation

### Prerequisites

- Python 3.10+
- pip, poetry, or [uv](https://github.com/astral-sh/uv)
- zbar shared library (for QR image scanning):
  - **macOS**: `brew install zbar`
  - **Ubuntu/Debian**: `sudo apt-get install libzbar0`
  - **Windows**: Install the zbar runtime and ensure its DLL is on `PATH`

### Install Dependencies

```bash
# Using pip
pip install -e ".[dev]"

# Using uv
uv sync

# Using poetry
poetry install
```

### Run the App

```bash
# Desktop mode
python3 -m src.main

# Console script (after pip install)
two-fa

# Using flet CLI
flet run src/main.py
```

### Build Android APK

```bash
flet build apk
```

The generated APK will be in the `build/apk/` directory.

## 📂 Project Structure

```
2FA/
├── main.py                    # Flet build entry point
├── pyproject.toml             # Project configuration & dependencies
├── src/
│   ├── main.py                # App entry point
│   ├── config.py              # Configuration management
│   ├── core/                  # Core business logic
│   │   ├── otp.py             # TOTP/HOTP generation & verification
│   │   ├── crypto.py          # Encryption (Argon2id + Fernet)
│   │   ├── vault.py           # Encrypted vault management
│   │   ├── uri_parser.py      # otpauth:// URI parsing
│   │   └── qr.py              # QR code scanning & generation
│   ├── github/                # GitHub integration
│   │   ├── oauth.py           # GitHub OAuth (Device Flow)
│   │   └── api.py             # GitHub REST API client
│   ├── storage/               # Data persistence
│   │   ├── models.py          # SQLModel data models
│   │   └── database.py        # SQLite connection
│   ├── ui/                    # Flet UI layer
│   │   ├── app.py             # Main app with routing
│   │   ├── theme.py           # Material Design 3 theme
│   │   ├── pages/             # App pages (home, lock, settings, etc.)
│   │   └── components/        # Reusable UI components
│   └── utils/                 # Utilities
│       ├── clipboard.py       # Clipboard with auto-clear
│       ├── time_sync.py       # NTP time sync check
│       └── export_import.py   # Data import/export
├── extensions/
│   └── flet_qr_scanner/       # Local Flet extension for QR scanning
└── tests/                     # Unit tests
```

## 🔐 Security Design

| Feature | Implementation |
|---------|---------------|
| Master Key | Argon2id (memory=64MB, iterations=3, parallelism=4) |
| Encryption | Fernet (AES-128-CBC + HMAC-SHA256) per secret |
| Verification | Encrypted token validates password on unlock |
| Auto-lock | Configurable timeout (default 5 min) |
| Clipboard | Auto-clear after 30 seconds |
| Brute force | Lockout after 5 failed attempts |

## 📖 Usage

### Adding an Account

1. Tap the **+** button on the home screen
2. Choose a method:
   - **Manual** — Enter issuer, account name, and secret key
   - **Scan QR** — Scan from camera or select an image file
   - **Paste URI** — Paste an `otpauth://` URI

### Using 2FA Codes

1. Find your account in the list
2. Tap to copy the current code
3. Paste into the login form

### GitHub Device Flow

1. Go to **Settings** → Set GitHub Client ID and Client Secret
2. Go to **GitHub** tab → tap **Connect GitHub**
3. Enter the displayed code at [github.com/login/device](https://github.com/login/device)
4. Authorize the app

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_otp.py
```

## 📋 References

- [RFC 6238 — TOTP](https://tools.ietf.org/html/rfc6238)
- [RFC 4226 — HOTP](https://tools.ietf.org/html/rfc4226)
- [Key URI Format](https://github.com/google/google-authenticator/wiki/Key-Uri-Format)
- [Aegis Authenticator](https://github.com/beemdevelopment/Aegis) — Vault design reference
- [2FAuth](https://github.com/Bubka/2FAuth) — UI design reference
- [pyotp](https://github.com/pyauth/pyotp) — OTP implementation reference

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div id="中文"></div>

# 🔐 2FA 验证器

**中文** | [English](#-2fa-authenticator)

一款基于 Python 和 Flet 构建的安全两步验证 (2FA) 应用，支持加密存储和 GitHub 集成。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/Flet-Flutter%20based-purple.svg)](https://flet.dev)

## ✨ 功能特性

- 🔑 **TOTP/HOTP 支持** — 生成和验证基于时间和计数器的一次性密码（RFC 6238 / RFC 4226）
- 🔒 **加密保险库** — 所有密钥使用 Argon2id 密钥派生 + AES-128-CBC (Fernet) 加密存储
- 🐙 **GitHub 集成** — OAuth 设备流程、2FA 状态检查、账户管理
- 📷 **二维码支持** — 支持摄像头扫描（移动端）和图片文件识别，可生成二维码
- 📦 **导入/导出** — 兼容 Google Authenticator、Aegis Authenticator 及通用 `otpauth://` URI 格式
- 🎨 **Material Design 3** — 基于 Flet（Flutter）的现代简洁界面
- 🔐 **自动锁定** — 可配置的闲置超时后自动锁定保险库
- 📋 **剪贴板自动清除** — 复制的验证码在 30 秒后自动清除
- 🛡️ **暴力破解防护** — 连续 5 次密码错误后锁定
- ⏰ **NTP 时间同步** — 检测时钟漂移，确保 OTP 生成准确

## 📱 支持平台

| 平台 | 状态 |
|------|------|
| Android | ✅ 主要目标平台 |
| macOS | ✅ 已支持 |
| Windows | ✅ 已支持 |
| Linux | ✅ 已支持 |
| iOS | 🔧 实验性支持 |
| Web | 🔧 实验性支持 |

## 📸 应用截图

> 即将更新

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| UI 框架 | [Flet](https://flet.dev)（基于 Flutter） |
| OTP 核心 | [pyotp](https://github.com/pyauth/pyotp) |
| 加密算法 | [cryptography](https://cryptography.io)（Fernet/AES） |
| 密钥派生 | [argon2-cffi](https://github.com/hynek/argon2-cffi) |
| 数据库 | SQLite + [SQLModel](https://sqlmodel.tiangolo.com) |
| 二维码 | [qrcode](https://github.com/lincolnloop/python-qrcode) + [pyzbar](https://github.com/NaturalHistoryMuseum/pyzbar) |
| HTTP 客户端 | [httpx](https://github.com/encode/httpx) |
| OAuth | [authlib](https://github.com/lepture/authlib) |

## 🚀 安装

### 前置要求

- Python 3.10+
- pip、poetry 或 [uv](https://github.com/astral-sh/uv)
- zbar 共享库（用于二维码图片扫描）：
  - **macOS**：`brew install zbar`
  - **Ubuntu/Debian**：`sudo apt-get install libzbar0`
  - **Windows**：安装 zbar 运行时并确保其 DLL 在 `PATH` 中

### 安装依赖

```bash
# 使用 pip
pip install -e ".[dev]"

# 使用 uv
uv sync

# 使用 poetry
poetry install
```

### 运行应用

```bash
# 桌面模式
python3 -m src.main

# 命令行快捷方式（pip install 后）
two-fa

# 使用 flet CLI
flet run src/main.py
```

### 构建 Android APK

```bash
flet build apk
```

生成的 APK 文件位于 `build/apk/` 目录。

## 📂 项目结构

```
2FA/
├── main.py                    # Flet 构建入口
├── pyproject.toml             # 项目配置与依赖
├── src/
│   ├── main.py                # 应用入口
│   ├── config.py              # 配置管理
│   ├── core/                  # 核心业务逻辑
│   │   ├── otp.py             # TOTP/HOTP 生成与验证
│   │   ├── crypto.py          # 加密（Argon2id + Fernet）
│   │   ├── vault.py           # 加密保险库管理
│   │   ├── uri_parser.py      # otpauth:// URI 解析
│   │   └── qr.py              # 二维码扫描与生成
│   ├── github/                # GitHub 集成
│   │   ├── oauth.py           # GitHub OAuth（设备流程）
│   │   └── api.py             # GitHub REST API 客户端
│   ├── storage/               # 数据持久化
│   │   ├── models.py          # SQLModel 数据模型
│   │   └── database.py        # SQLite 连接
│   ├── ui/                    # Flet UI 层
│   │   ├── app.py             # 主应用与路由
│   │   ├── theme.py           # Material Design 3 主题
│   │   ├── pages/             # 应用页面（首页、锁定、设置等）
│   │   └── components/        # 可复用 UI 组件
│   └── utils/                 # 工具类
│       ├── clipboard.py       # 剪贴板自动清除
│       ├── time_sync.py       # NTP 时间同步检查
│       └── export_import.py   # 数据导入/导出
├── extensions/
│   └── flet_qr_scanner/       # 本地 Flet 二维码扫描扩展
└── tests/                     # 单元测试
```

## 🔐 安全设计

| 功能 | 实现方式 |
|------|---------|
| 主密钥 | Argon2id（内存=64MB，迭代=3，并行度=4） |
| 加密方式 | Fernet（AES-128-CBC + HMAC-SHA256）逐密钥加密 |
| 密码验证 | 加密令牌验证解锁密码 |
| 自动锁定 | 可配置超时（默认 5 分钟） |
| 剪贴板 | 30 秒后自动清除 |
| 暴力破解 | 5 次失败后锁定 |

## 📖 使用说明

### 添加账户

1. 在首页点击 **+** 按钮
2. 选择添加方式：
   - **手动输入** — 输入发行方、账户名和密钥
   - **扫描二维码** — 从摄像头扫描或选择图片文件
   - **粘贴 URI** — 粘贴 `otpauth://` URI

### 使用 2FA 验证码

1. 在列表中找到目标账户
2. 点击复制当前验证码
3. 粘贴到登录表单中

### GitHub 设备流程

1. 进入 **设置** → 设置 GitHub Client ID 和 Client Secret
2. 进入 **GitHub** 标签页 → 点击 **连接 GitHub**
3. 在 [github.com/login/device](https://github.com/login/device) 输入显示的验证码
4. 授权应用

## 🧪 运行测试

```bash
# 运行所有测试
pytest

# 运行并生成覆盖率报告
pytest --cov=src

# 运行指定测试文件
pytest tests/test_otp.py
```

## 📋 参考资料

- [RFC 6238 — TOTP](https://tools.ietf.org/html/rfc6238)
- [RFC 4226 — HOTP](https://tools.ietf.org/html/rfc4226)
- [Key URI Format](https://github.com/google/google-authenticator/wiki/Key-Uri-Format)
- [Aegis Authenticator](https://github.com/beemdevelopment/Aegis) — 保险库设计参考
- [2FAuth](https://github.com/Bubka/2FAuth) — UI 设计参考
- [pyotp](https://github.com/pyauth/pyotp) — OTP 实现参考

## 📄 开源协议

本项目基于 [MIT 协议](LICENSE) 开源。
