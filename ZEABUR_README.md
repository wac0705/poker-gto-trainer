# Zeabur 部署指南

## 關於 Zeabur

Zeabur 是一個現代化的雲端部署平台，支持自動部署、自定義域名、環境變數配置等功能。

## 部署方法

### 方法一：從 Git 倉庫部署（推薦）

1. **將代碼推送到 Git 倉庫**
   ```bash
   # 初始化 Git 倉庫（如果尚未初始化）
   git init
   git add .
   git commit -m "Initial commit: Texas Hold'em GTO Trainer"
   
   # 推送到 GitHub/GitLab
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **連接 Zeabur**
   - 訪問 [Zeabur Dashboard](https://dash.zeabur.com)
   - 登入您的帳戶（可使用 GitHub 登入）
   - 點擊 "New Project"
   - 選擇 "Deploy from Git"
   - 選擇您的倉庫和分支

3. **配置服務**
   - Zeabur 會自動檢測到 Dockerfile
   - 服務名稱：`poker-gto-trainer`
   - 端口會自動配置（使用 PORT 環境變數）

4. **部署完成**
   - 等待建置和部署完成
   - Zeabur 會提供一個公開的 URL

### 方法二：直接上傳代碼

1. **打包代碼**
   ```bash
   # 創建 zip 檔案，排除不必要的檔案
   zip -r poker-gto-trainer.zip . -x "*.git*" "*__pycache__*" "*.pyc"
   ```

2. **上傳到 Zeabur**
   - 在 Zeabur Dashboard 中選擇 "Upload Code"
   - 上傳 zip 檔案
   - 選擇 "Docker" 作為建置方式

### 方法三：使用 Zeabur CLI

1. **安裝 Zeabur CLI**
   ```bash
   npm install -g @zeabur/cli
   ```

2. **登入並部署**
   ```bash
   zeabur auth login
   zeabur deploy
   ```

## 環境變數配置

在 Zeabur Dashboard 中，您可以配置以下環境變數：

- `PORT`: 應用程式端口（Zeabur 會自動設置）
- `STREAMLIT_SERVER_PORT`: Streamlit 服務端口
- `STREAMLIT_SERVER_ADDRESS`: 服務地址（設為 0.0.0.0）

## 自定義域名

1. 在 Zeabur Dashboard 中選擇您的服務
2. 點擊 "Domains" 標籤
3. 添加您的自定義域名
4. 配置 DNS 記錄指向 Zeabur 提供的 CNAME

## 監控和日誌

- **查看日誌**: 在 Zeabur Dashboard 中點擊 "Logs"
- **監控狀態**: 在 "Overview" 中查看服務狀態
- **重新部署**: 點擊 "Redeploy" 按鈕

## 費用說明

- **免費額度**: Zeabur 提供免費額度，適合小型專案
- **付費方案**: 根據使用量計費，支持更高的流量和資源

## 自動部署

當您推送代碼到連接的 Git 倉庫時，Zeabur 會自動觸發重新部署：

```bash
git add .
git commit -m "Update poker trainer"
git push origin main
```

## 故障排除

### 建置失敗
- 檢查 Dockerfile 語法
- 確認所有依賴檔案都已包含
- 查看建置日誌中的錯誤訊息

### 應用程式無法啟動
- 檢查 `requirements.txt` 是否正確
- 確認 Python 代碼沒有語法錯誤
- 查看應用程式日誌

### 無法訪問應用程式
- 確認端口配置正確
- 檢查防火牆設置
- 確認域名解析正確

## 安全注意事項

- 不要在代碼中硬編碼敏感信息
- 使用環境變數存儲配置
- 定期更新依賴套件
- 考慮添加身份驗證機制

## 優勢

✅ **簡單部署**: 一鍵部署，無需複雜配置  
✅ **自動 HTTPS**: 自動配置 SSL 證書  
✅ **Git 整合**: 代碼推送自動部署  
✅ **監控工具**: 內建日誌和監控  
✅ **擴展性**: 支持自動擴展  
✅ **自定義域名**: 支持自定義域名  

開始享受您的德州撲克 GTO 訓練器在雲端的運行吧！🃏