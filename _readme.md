# FCL Release Sync

这个仓库包含一个GitHub工作流，用于自动同步FoldCraftLauncher的最新发布版到WebDAV存储。

## 工作流功能

- 每6小时自动检查FoldCraftLauncher的最新发布版
- 支持手动触发同步
- 自动下载Linux AppImage和Windows exe版本
- 将文件上传到WebDAV存储
- 保存发布说明到文件

## 设置步骤

### 1. 配置GitHub Secrets

在仓库的 `Settings` → `Secrets and variables` → `Actions` 中添加以下密钥：

- `WEBDAV_USERNAME`: WebDAV用户名 (wzmwayne@hotmail.com)
- `WEBDAV_PASSWORD`: WebDAV密码 (从GitHub仓库的"密钥"部分获取)
- `WEBDAV_URL`: WebDAV地址 (https://v3.111pan.cn/dav)

### 2. 工作流位置

工作流文件位于 `.github/workflows/fcl-release-sync.yml`

### 3. WebDAV结构

上传后的文件结构：
```
https://v3.111pan.cn/dav/
├── FoldCraftLauncher-vX.X.X.AppImage
├── FoldCraftLauncher-vX.X.X.exe
├── release_notes_vX.X.X.md
└── [版本号]/
    ├── FoldCraftLauncher-vX.X.X.AppImage
    ├── FoldCraftLauncher-vX.X.X.exe
    └── release_notes_vX.X.X.md
```

## 手动触发

可以在GitHub Actions页面手动触发工作流运行。

## 注意事项

- 工作流会自动清理下载的临时文件
- 支持多种平台的发布版本
- 会保留所有历史版本的文件