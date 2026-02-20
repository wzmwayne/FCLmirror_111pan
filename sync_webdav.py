#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import re
from pathlib import Path

def run_command(cmd, check=True):
    """执行shell命令"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        if result.stdout:
            print(result.stdout)
        if result.stderr and check:
            print(result.stderr, file=sys.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd}")
        print(f"Error: {e.stderr}", file=sys.stderr)
        if check:
            sys.exit(1)
        return e

def get_version_files():
    """获取所有版本相关的文件"""
    files = {}
    
    # 获取所有版本标签
    all_files = os.listdir('.')
    version_pattern = re.compile(r'^FoldCraftLauncher-(.+)\.(AppImage|exe|apk|md)$')
    
    for f in all_files:
        match = version_pattern.match(f)
        if match:
            version = match.group(1)
            file_type = match.group(2)
            if version not in files:
                files[version] = {}
            files[version][file_type] = f
    
    return files

def download_all_releases():
    """自动下载所有FCL版本"""
    print("Downloading all FCL releases...")
    
    # 获取所有发布版信息
    import json
    import urllib.request
    import urllib.error
    
    try:
        # 获取所有发布版
        with urllib.request.urlopen('https://api.github.com/repos/FCL-Team/FoldCraftLauncher/releases') as response:
            releases = json.loads(response.read().decode())
        
        downloaded_count = 0
        
        for release in releases:
            tag_name = release.get('tag_name', '')
            if not tag_name:
                continue
                
            print(f"\nProcessing release: {tag_name}")
            
            # 保存发布说明
            body = release.get('body', '')
            if body:
                with open(f'release_notes_{tag_name}.md', 'w', encoding='utf-8') as f:
                    f.write(body)
                print(f"  Saved release notes for {tag_name}")
            
            # 下载所有资产
            assets = release.get('assets', [])
            for asset in assets:
                asset_name = asset.get('name', '')
                download_url = asset.get('browser_download_url', '')
                
                if not download_url or not asset_name:
                    continue
                
                # 确定文件类型
                if asset_name.endswith(('.AppImage', '.apk')):
                    file_type = 'AppImage' if 'AppImage' in asset_name else 'apk'
                elif asset_name.endswith('.exe'):
                    file_type = 'exe'
                else:
                    continue
                
                # 下载文件
                output_filename = f'FoldCraftLauncher-{tag_name}.{file_type}'
                try:
                    with urllib.request.urlopen(download_url) as response:
                        with open(output_filename, 'wb') as out_file:
                            out_file.write(response.read())
                    print(f"  Downloaded: {output_filename}")
                    downloaded_count += 1
                except Exception as e:
                    print(f"  Failed to download {asset_name}: {e}")
        
        print(f"\nDownloaded {downloaded_count} files")
        return True
        
    except Exception as e:
        print(f"Error downloading releases: {e}")
        return False

def cleanup_old_versions(current_versions, max_versions=3):
    """清理旧版本，只保留最新的max_versions个版本"""
    if len(current_versions) <= max_versions:
        return current_versions
    
    # 按版本号排序（简单排序）
    sorted_versions = sorted(current_versions, reverse=True)
    keep_versions = sorted_versions[:max_versions]
    
    print(f"Keeping latest {max_versions} versions: {keep_versions}")
    
    return keep_versions

def sync_to_webdav():
    """同步文件到WebDAV"""
    # 检查WebDAV配置
    webdav_username = os.getenv('WEBDAV_USERNAME')
    webdav_password = os.getenv('WEBDAV_PASSWORD')
    webdav_url = os.getenv('WEBDAV_URL')
    
    if not all([webdav_username, webdav_password, webdav_url]):
        print("Error: WebDAV credentials not set in environment variables")
        sys.exit(1)
    
    print(f"Syncing to WebDAV: {webdav_url}")
    
    # 先下载所有版本
    if not download_all_releases():
        print("Failed to download releases")
        return
    
    # 获取所有版本文件
    all_files = get_version_files()
    if not all_files:
        print("No version files found")
        return
    
    print(f"Found {len(all_files)} versions: {list(all_files.keys())}")
    
    # 清理旧版本
    current_versions = list(all_files.keys())
    keep_versions = cleanup_old_versions(current_versions, max_versions=3)
    
    # 只保留需要的版本
    files_to_keep = {v: all_files[v] for v in keep_versions if v in all_files}
    
    # 创建WebDAV临时目录
    webdav_mount = '/mnt/webdav'
    
    try:
        # 安装davfs2
        run_command('sudo apt-get update && sudo apt-get install -y davfs2', check=False)
        
        # 创建挂载点
        run_command(f'sudo mkdir -p {webdav_mount}')
        
        # 挂载WebDAV
        print("Mounting WebDAV...")
        result = run_command(f'sudo mount -t davfs "{webdav_url}" {webdav_mount}')
        if result.returncode != 0:
            print("Failed to mount WebDAV, trying with credentials...")
            # 尝试使用临时挂载
            run_command(f'echo "{webdav_username}:{webdav_password}" | sudo tee /etc/davfs2/secrets > /dev/null')
            run_command('sudo chmod 600 /etc/davfs2/secrets')
            run_command(f'sudo mount -t davfs "{webdav_url}" {webdav_mount}')
        
        # 创建版本目录并上传文件
        for version, file_dict in files_to_keep.items():
            print(f"\nProcessing version: {version}")
            
            # 创建版本目录
            version_dir = os.path.join(webdav_mount, version)
            run_command(f'sudo mkdir -p "{version_dir}"')
            
            # 上传所有相关文件
            for file_type, filename in file_dict.items():
                if os.path.exists(filename):
                    dest_path = os.path.join(version_dir, filename)
                    run_command(f'sudo cp "{filename}" "{dest_path}"')
                    print(f"  Uploaded: {filename}")
                else:
                    print(f"  Warning: {filename} not found")
            
            # 复制到根目录（可选）
            run_command(f'sudo cp -r "{version_dir}"/* "{webdav_mount}/"')
        
        print("\nUpload completed successfully!")
        
    except Exception as e:
        print(f"Error during sync: {e}")
        sys.exit(1)
    finally:
        # 卸载WebDAV
        try:
            run_command(f'sudo umount {webdav_mount}')
            print("WebDAV unmounted")
        except:
            pass

if __name__ == '__main__':
    sync_to_webdav()