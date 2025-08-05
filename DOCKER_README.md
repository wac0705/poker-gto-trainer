# Docker 部署說明

## 前置需求

1. 安裝 Docker Desktop
   - 下載地址：https://www.docker.com/products/docker-desktop
   - 安裝後確保 Docker 服務正在運行

## 快速開始

### 方法一：使用批次檔案（Windows）

1. **啟動應用程式**
   ```bash
   # 雙擊執行
   run_docker.bat
   ```

2. **停止應用程式**
   ```bash
   # 雙擊執行
   stop_docker.bat
   ```

### 方法二：使用命令行

1. **建置和啟動**
   ```bash
   # 建置 Docker 鏡像
   docker-compose build
   
   # 啟動容器（背景執行）
   docker-compose up -d
   ```

2. **訪問應用程式**
   - 在瀏覽器中打開：http://localhost:8501

3. **查看日誌**
   ```bash
   docker-compose logs -f
   ```

4. **停止容器**
   ```bash
   docker-compose down
   ```

## 其他有用命令

```bash
# 查看容器狀態
docker-compose ps

# 重新建置鏡像
docker-compose build --no-cache

# 進入容器內部（調試用）
docker-compose exec poker-gto-trainer bash

# 移除所有相關容器和鏡像
docker-compose down --rmi all
```

## 端口說明

- **8501**: Streamlit 應用程式端口
- 可以在 `docker-compose.yml` 中修改端口映射

## 資料持久化

如果需要保存遊戲數據，可以在 `docker-compose.yml` 中取消註解 volumes 部分：

```yaml
volumes:
  - ./data:/app/data
```

## 故障排除

1. **容器無法啟動**
   - 檢查 Docker Desktop 是否運行
   - 檢查端口 8501 是否被其他程式佔用

2. **無法訪問應用程式**
   - 等待容器完全啟動（約 30-60 秒）
   - 檢查 `docker-compose logs` 輸出

3. **建置失敗**
   - 確保網路連接正常（需要下載 Python 套件）
   - 嘗試 `docker-compose build --no-cache`