"""
缩绒客户管理系统 - 启动入口 (用于PyInstaller打包)
启动后自动打开浏览器访问本系统
"""
import sys
import os
import webbrowser
import threading
import time

# 解决PyInstaller打包后的路径问题
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

def open_browser():
    """延迟打开浏览器，等待Flask启动"""
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5800')

if __name__ == '__main__':
    from app import app

    print('=' * 50)
    print('  缩绒客户管理系统')
    print(f'  数据目录: {BASE_DIR}')
    print('=' * 50)
    print('  启动中...')
    print('  浏览器自动打开中...')
    print()
    print('  访问地址: http://127.0.0.1:5800')
    print('  关闭窗口即可停止服务')
    print('=' * 50)

    # 在新线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()

    # 启动Flask
    app.run(
        debug=False,
        host='127.0.0.1',  # 只用localhost，更安全
        port=5800
    )
