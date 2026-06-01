@echo off
chcp 65001 >nul
echo ========================================
echo  缩绒客户管理系统 - 打包为EXE
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 安装依赖包...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo [2/4] 检查PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo [3/4] 打包中（约2-5分钟）...
pyinstaller --clean --onefile --name "缩绒客户管理系统" ^
    --add-data "templates;templates" ^
    --hidden-import flask ^
    --hidden-import xlrd ^
    --hidden-import sqlite3 ^
    --hidden-import datetime ^
    --hidden-import csv ^
    --hidden-import io ^
    --hidden-import webbrowser ^
    --hidden-import threading ^
    run.py

if %errorlevel% neq 0 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo [4/4] 打包完成！
echo.
echo 输出文件: dist\缩绒客户管理系统.exe
echo.
echo 使用说明:
echo   1. 双击 "缩绒客户管理系统.exe" 即可运行
echo   2. 程序会自动打开浏览器
echo   3. 数据库文件 suorong.db 会在 exe 同目录下生成
echo   4. 如需导入新数据，启动后点击"导入数据"功能
echo.

pause
