# USTC-webtools

中国科学技术大学 (USTC) 常用网络工具集。

## 📦 环境配置 (使用 uv)

本项目使用 [uv](https://github.com/astral-sh/uv) 进行极速包管理。

### 1. 安装 uv
如果你还没有安装 uv，请先安装：

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 安装依赖
在项目根目录下运行：

```bash
# 创建虚拟环境并安装所有依赖
uv sync
```

### 3. 运行程序
使用 `uv run` 执行脚本，它会自动使用配置好的虚拟环境：

```bash
uv run main.py
```

---

## 🔧 配置详解与原理

### 1. 浏览器 (Chrome) 在哪里？
**原理**：Selenium 会自动在操作系统的默认安装路径下查找 Chrome 浏览器。
- **Windows**: 通常在 `C:\Program Files\Google\Chrome\Application\chrome.exe` 或 `C:\Program Files (x86)\...`。
- **配置方法**：
  - 如果你的 Chrome 安装在默认位置，**无需任何配置**。
  - 如果安装在非标准位置，需要修改 `jwc/Login.py` 中的 `login_by_selenium` 函数，添加 `binary_location`：
    ```python
    options = Options()
    options.binary_location = r"D:\你的\Chrome\路径\chrome.exe"
    ```

### 2. 驱动器 (ChromeDriver) 在哪里？
**原理**：本项目集成了 `webdriver-manager` 库。
- **自动管理**：你**不需要**手动下载或配置驱动。
- **存放位置**：驱动文件会被自动下载到用户目录下的 `.wdm` 文件夹中。
  - Windows 路径示例：`C:\Users\你的用户名\.wdm\drivers\chromedriver\win64\...`
- **运行逻辑**：每次运行时，程序会检查当前 Chrome 版本，自动下载或调用对应的驱动版本，彻底解决版本不兼容报错。

### 3. 浏览器的缓存 (User Data) 在哪里？
**原理**：
- **默认情况**：Selenium 每次启动都会在系统的**临时文件夹** (`%TEMP%`) 创建一个新的、干净的浏览器配置文件。当脚本运行结束（`driver.quit()`）时，这个临时文件夹会被自动删除。这意味着每次登录都是全新的，没有历史记录。
- **自定义持久化**：如果你希望保留登录状态、缓存或插件信息，需要指定一个固定的目录。

**配置方法**：
打开 `jwc/Login.py`，找到 `login_by_selenium` 函数，取消注释并修改以下代码：

```python
# 修改为你想要的缓存保存路径
# 注意：路径中使用 / 或 \\，不要用单斜杠 \
options.add_argument(f"--user-data-dir=D:/Code/ChromeCache/default")
```

**⚠️ 注意**：如果指定了自定义缓存目录，且你手动打开了一个使用该配置文件的 Chrome 窗口，Selenium 可能会因为文件被占用而启动失败。
