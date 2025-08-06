# 德州撲克 GTO 訓練器 - 主入口檔案
# Texas Hold'em GTO Trainer - Main Entry Point

"""
這是 Zeabur 部署的主入口檔案
This is the main entry point for Zeabur deployment
"""

import sys
import os

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接導入並運行主程式
try:
    # 導入主程式模組
    from texas_holdem_enhanced_ui import *
    
    # 如果是直接執行這個檔案
    if __name__ == "__main__":
        # 執行主程式
        exec(open('texas_holdem_enhanced_ui.py').read())
        
except ImportError as e:
    print(f"導入錯誤: {e}")
    print("請確保所有依賴檔案都存在")
    sys.exit(1)
except FileNotFoundError as e:
    print(f"檔案錯誤: {e}")
    print("找不到 texas_holdem_enhanced_ui.py 檔案")
    sys.exit(1)
except Exception as e:
    print(f"未知錯誤: {e}")
    sys.exit(1)