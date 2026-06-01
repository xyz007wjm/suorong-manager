@echo off
chcp 65001 >nul
echo ========================================
echo  缩绒客户管理系统
echo  浏览器打开后请勿关闭此窗口
echo ========================================
echo.
python run.py
if %errorlevel% neq 0 (
    echo.
    echo 启动失败，请先运行 install_deps.bat 安装依赖
    pause
)
