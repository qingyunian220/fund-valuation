# 📈 基金实时估值系统

一个简洁美观的基金实时估值查询 Web 应用，支持多用户管理、基金搜索、实时估值等功能。

## ✨ 功能特性

- 🔐 **用户认证**：注册/登录系统，支持邀请码注册
- 🔍 **基金搜索**：实时搜索匹配基金代码和名称
- 📱 **响应式设计**：完美适配手机和电脑
- 💾 **基金收藏**：个人化管理自选基金
- ⏱️ **实时估值**：定时获取基金最新估值数据
- 📊 **涨跌展示**：直观显示涨跌颜色和百分比
- 🎨 **美观界面**：现代化的 UI 设计
- 🚀 **外网访问**：支持通过内网穿透工具分享给朋友

## 🛠️ 技术栈

- **后端**：Python + Flask
- **前端**：HTML + CSS + JavaScript
- **数据源**：天天基金网 API

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/fund-valuation.git
cd fund-valuation
```

### 2. 安装依赖

```bash
pip install flask flask-cors requests
```

### 3. 运行项目

```bash
python app.py
```

访问 http://localhost:5000 即可使用

## 📱 使用说明

### 首次登录

- 用户名：`admin`
- 密码：`123456`

### 注册用户

- 访问注册页面
- 输入邀请码（默认：`fund2026`）
- 完成注册

### 添加基金

- 在搜索框输入基金代码或名称
- 从搜索结果中选择要添加的基金
- 点击「添加基金」按钮

### 外网访问

推荐使用内网穿透工具（如花生壳、cpolar）将本地服务暴露到公网，方便分享给朋友使用。

## 🎨 项目截图

### 登录页面
- 支持记住登录状态（30天）
- 美观的背景图

### 主页面
- 简洁的基金列表
- 直观的涨跌显示
- 统一的估值时间展示

### 配置页面
- 管理员专属
- 可修改邀请码和管理员账号

## 📁 项目结构

```
fund-valuation/
├── app.py                    # 主应用
├── fund_valuation_test.py    # 基金数据获取
├── config.json              # 配置文件（自动生成）
├── users.json               # 用户数据（自动生成）
├── funds.json               # 基金数据（自动生成）
├── requirements.txt         # 依赖列表
├── README.md               # 项目说明
├── static/                 # 静态资源
│   └── manifest.json       # PWA配置
└── templates/              # 页面模板
    ├── index.html         # 主页面
    ├── login.html         # 登录页面
    ├── register.html      # 注册页面
    └── config.html        # 配置页面
```

## 🛡️ 安全提示

- 请修改默认管理员密码
- 生产环境建议使用 HTTPS
- 定期备份数据文件（users.json, funds.json, config.json）

## 📄 License

MIT License - 可自由使用和修改

## 🤝 贡献

欢迎 Issue 和 Pull Request！

---

⭐ 如果觉得好用，请给个 Star！
