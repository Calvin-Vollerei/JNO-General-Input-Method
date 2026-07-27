"""JNO通用输入法 入口"""
import sys
from tkinter import messagebox

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

def main():
    if not HAS_PIL:
        print("请先安装: pip install pillow")
        sys.exit(1)
    from app import App
    App().run()

if __name__ == "__main__":
    main()
