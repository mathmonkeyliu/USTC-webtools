# USTC-webtools

中国科学技术大学 (USTC) 脚本工具集。包括教务处的抢课、选课、换课自动化。

## 环境配置

本项目使用 [uv](https://github.com/astral-sh/uv) 进行包管理。

### 安装依赖
在项目根目录下运行：

```bash
uv sync
```

### Chrome

确保你的电脑里有Chrome浏览器，并且其路径在环境变量里。如果Chrome不在环境变量里，则需要修改 [jwc/Login.py](jwc/Login.py) 中的 `login_by_selenium` 函数，添加 `binary_location`：

```python
options = Options()
options.binary_location = r"D:\path\to\your\chrome.exe"
```

## 使用

### 抢课

使用抢课/选课功能，请参考[example_select_courses.py](example_select_courses.py)。

### 换课

使用换课功能，请参考[example_change_courses.py](example_change_courses.py)。
