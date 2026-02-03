import os
import time
import threading
from typing import Optional

from app.models.download import DownloadTask, DownloadStatus
from app.network.http_client import http_client
from app.services.api_service import api_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DownloadService:
    def __init__(self, download_dir: str = "Download"):
        self.download_dir = download_dir
        self.current_task: Optional[DownloadTask] = None
        self.preload_pool = []
        self.preload_size = 3
        self.lock = threading.RLock()
        
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"创建下载目录: {self.download_dir}")
    
    def get_random_api_name(self) -> Optional[str]:
        try:
            api_config = api_service.get_random_api()
            if not api_config:
                logger.error("没有可用的API")
                return None
            return api_config.name
        except Exception as e:
            logger.error(f"获取API失败: {str(e)}")
            return None
    
    def download(self, api_name: str, progress_callback=None) -> Optional[str]:
        try:
            api_config = api_service.get_api_by_name(api_name)
            if not api_config:
                logger.error(f"API {api_name} 不存在")
                return None
            
            image_url = None
            with self.lock:
                if self.preload_pool:
                    try:
                        image_url = self.preload_pool.pop(0)
                    except IndexError:
                        pass
            
            if not image_url:
                image_url = self._get_image_url(api_config)
                if not image_url:
                    for other_api in api_service.get_apis():
                        if other_api.name != api_name and other_api.enabled:
                            image_url = self._get_image_url(other_api)
                            if image_url:
                                break
                
                if not image_url:
                    logger.error("无法获取图片URL")
                    return None
            
            with self.lock:
                self.current_task = DownloadTask(
                    url=image_url,
                    status=DownloadStatus.DOWNLOADING,
                    api_name=api_name
                )
            
            def on_progress(progress, total_size):
                with self.lock:
                    if self.current_task:
                        self.current_task.progress = progress
                        self.current_task.total_size = total_size
                if progress_callback:
                    progress_callback(progress, total_size)
            
            save_path = self._download_image(image_url, api_name, on_progress)
            
            with self.lock:
                if self.current_task:
                    if save_path:
                        self.current_task.status = DownloadStatus.SUCCESS
                        self.current_task.save_path = save_path
                        logger.info(f"图片下载成功: {save_path}")
                    else:
                        self.current_task.status = DownloadStatus.FAILED
                        self.current_task.error_message = "下载失败"
                        logger.error("图片下载失败")
            
            self._preload_images()
            return save_path
        except Exception as e:
            logger.error(f"下载失败: {str(e)}")
            with self.lock:
                if self.current_task:
                    self.current_task.status = DownloadStatus.FAILED
                    self.current_task.error_message = str(e)
            return None
    
    def _get_image_url(self, api_config) -> Optional[str]:
        try:
            api_url = api_config.url
            if api_config.params:
                if "?" in api_url:
                    api_url = f"{api_url}&{api_config.params}"
                else:
                    api_url = f"{api_url}?{api_config.params}"
            
            response = http_client.get(api_url, allow_redirects=True)
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type or 'text/json' in content_type:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        if data.get('success') and 'data' in data:
                            return data.get('data')
                        elif 'url' in data:
                            return data.get('url')
                        elif 'image' in data:
                            return data.get('image')
                        elif 'img' in data:
                            return data.get('img')
                        elif 'data' in data and isinstance(data['data'], list) and data['data']:
                            first_item = data['data'][0]
                            if 'urls' in first_item and isinstance(first_item['urls'], dict):
                                if 'original' in first_item['urls']:
                                    return first_item['urls']['original'].strip()
                except Exception:
                    pass
            
            final_url = response.url
            if self._is_image_url(final_url):
                return final_url
            
            if 'text/html' in content_type:
                try:
                    import re
                    html_content = response.text
                    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html_content)
                    if img_match:
                        img_url = img_match.group(1)
                        if not img_url.startswith('http'):
                            from urllib.parse import urljoin
                            img_url = urljoin(api_url, img_url)
                        return img_url
                except Exception:
                    pass
            
            return None
        except Exception as e:
            logger.error(f"获取图片URL失败: {str(e)}")
            return None
    
    def _download_image(self, url: str, api_name: str, progress_callback=None) -> Optional[str]:
        try:
            response = http_client.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            ext = os.path.splitext(url)[1] or '.jpg'
            file_name = f"{timestamp}{ext}"
            save_path = os.path.join(self.download_dir, file_name)
            
            if os.path.exists(save_path):
                import random
                random_suffix = random.randint(1000, 9999)
                file_name = f"{timestamp}_{random_suffix}{ext}"
                save_path = os.path.join(self.download_dir, file_name)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0 and progress_callback:
                            progress = int((downloaded_size / total_size) * 100)
                            progress_callback(progress, total_size)
            
            if progress_callback:
                progress_callback(100, total_size)
            
            logger.info(f"图片下载成功: {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"下载图片失败: {str(e)}")
            return None
    
    def _preload_images(self):
        try:
            while True:
                with self.lock:
                    if len(self.preload_pool) >= self.preload_size:
                        break
                
                api_config = api_service.get_random_api()
                if not api_config:
                    time.sleep(1)
                    continue
                
                image_url = self._get_image_url(api_config)
                if image_url:
                    with self.lock:
                        if image_url not in self.preload_pool and len(self.preload_pool) < self.preload_size:
                            self.preload_pool.append(image_url)
                            time.sleep(0.5)
        except Exception as e:
            logger.error(f"预加载失败: {str(e)}")
    
    def _is_image_url(self, url: str) -> bool:
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return any(ext in url.lower() for ext in image_extensions)
    
    def get_status(self) -> Optional[DownloadStatus]:
        with self.lock:
            if self.current_task:
                return self.current_task.status
            return None
    
    def get_current_task(self) -> Optional[DownloadTask]:
        with self.lock:
            return self.current_task

# 导出默认下载服务实例
download_service = DownloadService()
