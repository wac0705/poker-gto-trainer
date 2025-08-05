# 德州撲克 GTO 訓練器 - 部署選項總覽

## 📦 可用的部署方式

### 1. 本地運行
```bash
# 雙擊執行
run_enhanced_game.bat
```
**優點**: 簡單快速，無需額外設置  
**適用**: 個人使用、開發測試

### 2. Docker 本地部署
```bash
# 雙擊執行
run_docker.bat
```
**優點**: 環境隔離，一致性部署  
**適用**: 團隊協作、穩定環境

### 3. Zeabur 雲端部署 ⭐ **推薦**
```bash
# 雙擊執行
deploy_to_zeabur.bat
```
**優點**: 
- ✅ 免費額度充足
- ✅ 自動 HTTPS
- ✅ Git 自動部署
- ✅ 自定義域名
- ✅ 無需管理伺服器

**適用**: 生產環境、分享給他人

## 🚀 快速開始 Zeabur 部署

1. **準備代碼**
   ```bash
   cd enhanced_version
   deploy_to_zeabur.bat
   ```

2. **推送到 GitHub**
   ```bash
   git remote add origin https://github.com/your-username/poker-gto-trainer.git
   git push -u origin main
   ```

3. **部署到 Zeabur**
   - 訪問 [dash.zeabur.com](https://dash.zeabur.com)
   - 點擊 "New Project" → "Deploy from Git"
   - 選擇您的倉庫
   - 自動部署完成！

## 📋 檔案說明

### 核心檔案
- `texas_holdem_enhanced_ui.py` - 主程式
- `texas_holdem_simple.py` - 遊戲邏輯
- `hand_evaluator.py` - 手牌評估
- `gto_ranges_clean.json` - GTO 策略資料

### 部署配置
- `Dockerfile` - Docker 容器配置
- `docker-compose.yml` - Docker Compose 配置
- `zeabur.json` - Zeabur 部署配置
- `requirements.txt` - Python 依賴

### 輔助檔案
- `run_enhanced_game.bat` - 本地啟動
- `run_docker.bat` - Docker 啟動
- `deploy_to_zeabur.bat` - Zeabur 部署準備
- `.gitignore` - Git 忽略檔案
- 各種 README 文件

## 🔧 環境需求

### 本地運行
- Python 3.11+
- Streamlit
- 其他依賴見 `requirements.txt`

### Docker 運行  
- Docker Desktop

### Zeabur 部署
- Git 帳戶 (GitHub/GitLab)
- Zeabur 帳戶 (免費)

## 💡 選擇建議

| 使用場景 | 推薦方式 | 理由 |
|---------|---------|------|
| 個人學習 | 本地運行 | 最簡單 |
| 團隊開發 | Docker | 環境一致 |
| 生產使用 | Zeabur | 穩定可靠 |
| 分享展示 | Zeabur | 公開訪問 |

開始您的德州撲克 GTO 訓練之旅吧！🃏♠️♥️♦️♣️