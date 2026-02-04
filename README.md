# 🔞随机Setu下载器🔞

一个简单易用的随机图片下载工具，支持从多个API源获取随机r18图片并下载到本地。   
   
## 功能特点

- **多API源支持**：内置推荐API和本地API配置
- **可视化界面**：基于PyQt5的直观用户界面
- **实时下载进度**：显示下载进度条和状态信息
- **API管理**：支持启用/禁用、编辑API配置
- **预加载功能**：后台预加载图片，提升下载速度
- **配置持久化**：自动保存窗口位置和API配置

## 安装说明

### 环境要求

- Python 3.7+
- PyQt5
- requests

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python main.py
```

## 使用方法

1. **启动应用**：运行 `main.py` 文件
2. **选择API源**：
   - 从推荐API获取：使用内置的推荐API列表
   - 从本地apis.txt获取：使用本地配置的API列表
3. **点击下载**：点击"随机下载"按钮开始下载图片
4. **查看状态**：界面会显示下载状态和进度
5. **管理API**：点击"设置API"按钮打开API配置对话框

## 项目结构

```
.
├── app/
│   ├── config/          # 配置管理
│   ├── models/          # 数据模型
│   ├── network/         # 网络请求
│   ├── services/        # 业务逻辑
│   ├── ui/              # 用户界面
│   ├── utils/           # 工具函数
│   └── __init__.py
├── main.py              # 应用入口
├── README.md            # 项目文档
└── requirements.txt     # 依赖文件
```

## 核心模块说明

### 1. API服务 (`app/services/api_service.py`)
- 加载和管理API配置
- 支持从推荐URL或本地文件加载API
- 提供随机API选择功能

### 2. 下载服务 (`app/services/download_service.py`)
- 从API获取图片URL
- 下载图片到本地目录
- 支持预加载图片提升性能

### 3. 配置服务 (`app/services/config_service.py`)
- 管理应用配置
- 保存和加载API配置
- 持久化窗口位置等设置

### 4. 网络客户端 (`app/network/http_client.py`)
- 封装HTTP请求
- 支持重试机制
- 管理HTTP会话

## 配置说明

### API配置

#### 本地API文件格式 (`apis.txt`)

```
# 示例API配置
!exAPI:http://example.com/api|1|{说明}#注释
!代表支持传入参数
http/https之前的":"之前即为自定义的api名称（若第一位是"!"则不包括"!"）
api链接后的"|数字|"为权重，数字/所有api数字之和 即为api随机到的概率
{}里为api设置界面api名称后括号里的内容，不添加则无括号（用于说明）
#为注释
```

- `!` 前缀表示API支持参数
- `{描述}` 可选的API描述
- `| 权重` 可选的API权重（影响随机选择概率）

### 应用配置

应用配置会自动保存到本地，包括：
- 窗口位置和大小
- API启用状态
- API参数配置

## 注意事项

1. 请确保网络连接正常
2. 部分API可能需要特定参数才能正常工作
3. 下载的图片会保存在 `Download` 目录中
4. 首次运行时会自动创建必要的目录结构

## 常见问题

### Q: 下载失败怎么办？
A: 请检查网络连接，或尝试切换到其他API源。

### Q: 如何添加自定义API？
A: 在 `apis.txt` 文件中添加API地址，或在API设置对话框中添加。

### Q: 应用启动失败怎么办？
A: 请检查是否安装了所有依赖，或查看日志文件了解详细错误。

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开Pull Request




---

**免责声明**：本工具仅用于学习和研究目的，请遵守相关法律法规，合理使用。
