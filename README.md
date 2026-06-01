# 缩绒客户管理系统 v1.0

基于缩绒日报表的客户信息管理系统，支持数据录入、查询统计、导入导出。

## 功能特性

- **工作台** — 数据总览看板，应收/已收/未付统计，趋势图表，欠款排行
- **记录管理** — 多条件筛选、分页展示、增删改查
- **客户管理** — 客户汇总卡片，点击查看明细
- **数据导入** — 从 Excel 缩绒日报表一键导入
- **数据导出** — 导出为 CSV 格式

## 快速开始

### 方式一：下载 EXE（推荐）

1. 前往 [Releases](https://github.com/xyz007wjm/suorong-manager/releases) 或 Actions 页面下载最新编译的 `缩绒客户管理系统.exe`
2. 双击运行，自动打开浏览器

### 方式二：源码运行

```bash
pip install flask xlrd
python run.py
```

浏览器访问 http://127.0.0.1:5800

### 方式三：自行编译 EXE

在 Windows 上运行：

```bash
pip install pyinstaller flask xlrd
pyinstaller --clean --onefile --name "缩绒客户管理系统" --add-data "templates;templates" --hidden-import flask --hidden-import xlrd run.py
```

或在 GitHub 仓库 Actions 页面点击 **Run workflow** 自动编译。

## 技术栈

- **后端**: Python + Flask + SQLite
- **前端**: Bootstrap 5 + Chart.js
- **打包**: PyInstaller

## 版权

© [Jackwang](https://wangjinming.com)
