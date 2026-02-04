import os
import time
import threading
from typing import Optional
import aiohttp

from app.models.download import DownloadTask, DownloadStatus
from app.network.http_client import http_client
from app.services.api_service import api_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DownloadService:
    def __init__(self, download_dir: str = "Download"):
        self.download_dir = download_dir
        self.current_task: Optional[DownloadTask] = None
        self.is_downloading = False  # 标记是否正在下载
        self.preload_pool = []  # 存储元组 (image_url, api_name)
        self.preload_size = 3
        self.api_cache_pool = []  # 存储随机API名称，最多5个
        self.api_cache_size = 5
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
    
    def download(self, progress_callback=None, api_change_callback=None) -> tuple[Optional[str], Optional[str]]:
        try:
            # 检查是否正在下载，防止并发下载
            with self.lock:
                if self.is_downloading:
                    logger.warning("正在下载中，请勿重复点击")
                    return None, None
                self.is_downloading = True
            
            image_url = None
            actual_api_name = None
            
            # 首先从预加载池获取
            with self.lock:
                if self.preload_pool:
                    try:
                        preload_item = self.preload_pool.pop(0)
                        image_url = preload_item[0]
                        actual_api_name = preload_item[1]
                        # 立即通知回调函数实际使用的API名称
                        if api_change_callback:
                            try:
                                api_change_callback(actual_api_name)
                            except Exception as e:
                                logger.error(f"调用API变化回调失败: {str(e)}")
                    except IndexError:
                        pass
                    except Exception as e:
                        logger.error(f"从预加载池获取失败: {str(e)}")
            
            # 如果预加载池为空，从API缓存池中获取API名称
            if not image_url or not actual_api_name:
                # 从API缓存池中取出一个API名称
                api_name = None
                with self.lock:
                    if self.api_cache_pool:
                        try:
                            api_name = self.api_cache_pool.pop(0)
                        except Exception as e:
                            logger.error(f"从API缓存池获取失败: {str(e)}")
                
                # 如果API缓存池为空，获取一个随机API
                if not api_name:
                    try:
                        api_config = api_service.get_random_api()
                        if not api_config:
                            logger.error("没有可用的API")
                            # 重置下载状态
                            try:
                                with self.lock:
                                    self.is_downloading = False
                            except Exception:
                                pass
                            return None, None
                        
                        actual_api_name = api_config.name
                        # 立即通知回调函数实际使用的API名称
                        if api_change_callback:
                            try:
                                api_change_callback(actual_api_name)
                            except Exception as e:
                                logger.error(f"调用API变化回调失败: {str(e)}")
                        image_url = self._get_image_url(api_config)
                    except Exception as e:
                        logger.error(f"获取随机API失败: {str(e)}")
                else:
                    # 使用从API缓存池中取出的API名称
                    try:
                        api_config = api_service.get_api_by_name(api_name)
                        if not api_config:
                            logger.error(f"API {api_name} 不存在")
                        else:
                            actual_api_name = api_config.name
                            # 立即通知回调函数实际使用的API名称
                            if api_change_callback:
                                try:
                                    api_change_callback(actual_api_name)
                                except Exception as e:
                                    logger.error(f"调用API变化回调失败: {str(e)}")
                            image_url = self._get_image_url(api_config)
                    except Exception as e:
                        logger.error(f"使用API缓存池中的API失败: {str(e)}")
                
                # 如果获取失败，尝试其他API
                if not image_url:
                    # 尝试从API缓存池中获取下一个API名称
                    try:
                        while True:
                            next_api_name = None
                            with self.lock:
                                if self.api_cache_pool:
                                    try:
                                        next_api_name = self.api_cache_pool.pop(0)
                                    except Exception as e:
                                        logger.error(f"从API缓存池获取失败: {str(e)}")
                            
                            if not next_api_name:
                                break
                            
                            next_api_config = api_service.get_api_by_name(next_api_name)
                            if not next_api_config:
                                continue
                            
                            # 立即通知回调函数实际使用的API名称
                            if api_change_callback:
                                try:
                                    api_change_callback(next_api_config.name)
                                except Exception as e:
                                    logger.error(f"调用API变化回调失败: {str(e)}")
                            
                            image_url = self._get_image_url(next_api_config)
                            if image_url:
                                actual_api_name = next_api_config.name
                                break
                    except Exception as e:
                        logger.error(f"尝试其他API失败: {str(e)}")
                    
                    # 如果API缓存池中没有更多API名称，尝试所有启用的API
                if not image_url:
                    try:
                        enabled_apis = [api for api in api_service.get_apis() if api.enabled]
                        if not enabled_apis:
                            logger.error("没有启用的API")
                            # 重置下载状态
                            try:
                                with self.lock:
                                    self.is_downloading = False
                            except Exception:
                                pass
                            return None, None
                        
                        for other_api in enabled_apis:
                            if other_api.name != actual_api_name:
                                # 立即通知回调函数实际使用的API名称
                                if api_change_callback:
                                    try:
                                        api_change_callback(other_api.name)
                                    except Exception as e:
                                        logger.error(f"调用API变化回调失败: {str(e)}")
                                
                                image_url = self._get_image_url(other_api)
                                if image_url:
                                    actual_api_name = other_api.name
                                    break
                    except Exception as e:
                        logger.error(f"尝试所有启用的API失败: {str(e)}")
                
                if not image_url:
                    logger.error("无法获取图片URL")
                    # 重置下载状态
                    try:
                        with self.lock:
                            self.is_downloading = False
                    except Exception:
                        pass
                    return None, None
            

            
            # 创建下载任务
            try:
                with self.lock:
                    self.current_task = DownloadTask(
                        url=image_url,
                        status=DownloadStatus.DOWNLOADING,
                        api_name=actual_api_name
                    )
            except Exception as e:
                logger.error(f"创建下载任务失败: {str(e)}")
            
            def on_progress(progress, total_size):
                try:
                    with self.lock:
                        if self.current_task:
                            self.current_task.progress = progress
                            self.current_task.total_size = total_size
                    if progress_callback:
                        progress_callback(progress, total_size)
                except Exception as e:
                    logger.error(f"进度回调失败: {str(e)}")
            
            # 下载图片
            save_path = None
            try:
                save_path = self._download_image(image_url, actual_api_name, on_progress)
            except Exception as e:
                logger.error(f"下载图片失败: {str(e)}")
            
            # 立即更新任务状态，不等待预加载
            try:
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
            except Exception as e:
                logger.error(f"更新任务状态失败: {str(e)}")
            
            # 异步执行预加载，不阻塞主线程
            try:
                preload_thread = threading.Thread(target=self._preload_images)
                preload_thread.daemon = True
                preload_thread.start()
            except Exception as e:
                logger.error(f"启动预加载线程失败: {str(e)}")
            finally:
                # 重置下载状态
                try:
                    with self.lock:
                        self.is_downloading = False
                except Exception:
                    pass
            
            return save_path, actual_api_name
        except Exception as e:
            logger.error(f"下载失败: {str(e)}")
            try:
                with self.lock:
                    if self.current_task:
                        self.current_task.status = DownloadStatus.FAILED
                        self.current_task.error_message = str(e)
            except Exception as e2:
                logger.error(f"更新任务状态失败: {str(e2)}")
            finally:
                # 重置下载状态
                try:
                    with self.lock:
                        self.is_downloading = False
                except Exception:
                    pass
            return None, None
    
    async def _get_image_url_async(self, api_config) -> Optional[str]:
        try:
            api_url = api_config.url
            if api_config.params:
                if "?" in api_url:
                    api_url = f"{api_url}&{api_config.params}"
                else:
                    api_url = f"{api_url}?{api_config.params}"
            
            response = await http_client.async_get(api_url)
            content_type = response.headers.get('Content-Type', '')
            
            # 处理直接返回图片的情况（内容类型为图片类型）
            if 'image/' in content_type:
                logger.info(f"直接返回图片: {response.url}")
                return response.url
            
            # 处理JSON响应的情况
            if 'application/json' in content_type or 'text/json' in content_type:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        # 处理有data字段的情况
                        if 'data' in data:
                            data_value = data['data']
                            
                            # 处理data为字符串的情况
                            if isinstance(data_value, str):
                                return data_value.strip()
                            
                            # 处理data为字典的情况
                            elif isinstance(data_value, dict):
                                # 检查字典中的url字段
                                if 'url' in data_value:
                                    return data_value['url'].strip()
                                # 检查字典中的urls字段
                                elif 'urls' in data_value and isinstance(data_value['urls'], dict):
                                    if 'original' in data_value['urls']:
                                        return data_value['urls']['original'].strip()
                            
                            # 处理data为列表的情况
                            elif isinstance(data_value, list) and data_value:
                                first_item = data_value[0]
                                if isinstance(first_item, dict):
                                    # 检查列表项中的url字段
                                    if 'url' in first_item:
                                        return first_item['url'].strip()
                                    # 检查列表项中的urls字段
                                    elif 'urls' in first_item and isinstance(first_item['urls'], dict):
                                        if 'original' in first_item['urls']:
                                            return first_item['urls']['original'].strip()
                        
                        # 处理直接有url字段的情况
                        elif 'url' in data:
                            return data.get('url').strip()
                        
                        # 处理有image字段的情况
                        elif 'image' in data:
                            return data.get('image').strip()
                        
                        # 处理有img字段的情况
                        elif 'img' in data:
                            return data.get('img').strip()
                except Exception as e:
                    logger.error(f"解析JSON失败: {str(e)}")
                    pass
            
            # 处理其他情况，检查最终的URL是否是图片URL
            final_url = response.url
            if self._is_image_url(final_url):
                return final_url
            
            if 'text/html' in content_type:
                try:
                    import re
                    html_content = response.text()
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
    
    def _run_async(self, coro):
        """运行异步函数并返回结果"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 如果当前线程没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    
    def _get_image_url(self, api_config) -> Optional[str]:
        try:
            return self._run_async(self._get_image_url_async(api_config))
        except Exception as e:
            logger.error(f"同步获取图片URL失败: {str(e)}")
            return None
    
    async def _download_image_async(self, url: str, api_name: str, progress_callback=None) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                session.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"
                })
                async with session.get(url) as response:
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
                        async for chunk in response.content.iter_chunked(8192):
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
    
    def _download_image(self, url: str, api_name: str, progress_callback=None) -> Optional[str]:
        try:
            return self._run_async(self._download_image_async(url, api_name, progress_callback))
        except Exception as e:
            logger.error(f"同步下载图片失败: {str(e)}")
            return None
    
    def _preload_images(self):
        try:
            # 限制预加载的最大尝试次数，避免无限循环
            max_attempts = 5
            
            # 首先填充API缓存池，确保有足够的随机API名称
            self._fill_api_cache_pool(max_attempts)
            
            # 然后从API缓存池中取出API名称，使用它们来获取图片URL
            self._preload_from_cache_pool(max_attempts)
            
            # 当图片链接缓存到缓存池后，继续缓存随机API名直到达到缓存大小
            self._fill_api_cache_pool(max_attempts)
        except Exception as e:
            logger.error(f"预加载失败: {str(e)}")
    
    def _fill_api_cache_pool(self, max_attempts):
        """填充API缓存池"""
        attempt_count = 0
        while attempt_count < max_attempts:
            try:
                with self.lock:
                    if len(self.api_cache_pool) >= self.api_cache_size:
                        break
                
                api_config = api_service.get_random_api()
                if not api_config:
                    time.sleep(0.1)
                    attempt_count += 1
                    continue
                
                with self.lock:
                    if api_config.name not in self.api_cache_pool and len(self.api_cache_pool) < self.api_cache_size:
                        self.api_cache_pool.append(api_config.name)
                        logger.info(f"添加API到缓存池: {api_config.name}")
                
                attempt_count += 1
            except Exception as e:
                logger.error(f"填充API缓存池失败: {str(e)}")
                attempt_count += 1
                time.sleep(0.1)
    
    def _preload_from_cache_pool(self, max_attempts):
        """从API缓存池中预加载图片"""
        attempt_count = 0
        while attempt_count < max_attempts:
            try:
                with self.lock:
                    if len(self.preload_pool) >= self.preload_size:
                        break
                    if not self.api_cache_pool:
                        break
                
                # 从API缓存池中取出一个API名称
                api_name = None
                with self.lock:
                    if self.api_cache_pool:
                        api_name = self.api_cache_pool.pop(0)
                
                if not api_name:
                    attempt_count += 1
                    continue
                
                api_config = api_service.get_api_by_name(api_name)
                if not api_config:
                    attempt_count += 1
                    continue
                
                # 尝试使用这个API获取图片URL
                image_url = self._get_image_url(api_config)
                if image_url:
                    preload_item = (image_url, api_config.name)
                    with self.lock:
                        if preload_item not in self.preload_pool and len(self.preload_pool) < self.preload_size:
                            self.preload_pool.append(preload_item)
                            logger.info(f"预加载图片: {image_url} (来自 {api_config.name})")
                else:
                    # 如果获取失败，尝试其他API
                    logger.warning(f"API {api_name} 获取图片失败，尝试其他API")
                
                attempt_count += 1
            except Exception as e:
                logger.error(f"从缓存池预加载失败: {str(e)}")
                attempt_count += 1
                time.sleep(0.1)
    
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
