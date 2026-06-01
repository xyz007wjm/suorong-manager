@echo off
chcp 65001 >nul
echo 正在安装依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% equ 0 (
    echo 安装完成！
) else (
    echo 安装失败，请检查Python是否正确安装
)
pause
