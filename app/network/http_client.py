import requests
import aiohttp
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.utils.logger import get_logger

logger = get_logger(__name__)

class HttpClient:
    def __init__(self, retries=3, backoff_factor=0.3, timeout=10):
        self.session = requests.Session()
        self.timeout = timeout
        
        retry_strategy = Retry(
            total=retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=backoff_factor
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置默认User-Agent头
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"
        })
    
    def get(self, url, **kwargs):
        try:
            logger.info(f"发送GET请求: {url}")
            response = self.session.get(url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            logger.info(f"GET请求成功: {url}, 状态码: {response.status_code}")
            return response
        except requests.RequestException as e:
            logger.error(f"GET请求失败: {url}, 错误: {str(e)}")
            raise
    
    def post(self, url, data=None, json=None, **kwargs):
        try:
            logger.info(f"发送POST请求: {url}")
            response = self.session.post(url, data=data, json=json, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            logger.info(f"POST请求成功: {url}, 状态码: {response.status_code}")
            return response
        except requests.RequestException as e:
            logger.error(f"POST请求失败: {url}, 错误: {str(e)}")
            raise
    
    async def async_get(self, url, **kwargs):
        try:
            logger.info(f"发送异步GET请求: {url}")
            async with aiohttp.ClientSession() as session:
                session.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"
                })
                async with session.get(url, timeout=self.timeout, **kwargs) as response:
                    response.raise_for_status()
                    content = await response.read()
                    # 模拟requests.Response对象
                    class AsyncResponse:
                        def __init__(self, status_code, content, headers, url):
                            self.status_code = status_code
                            self.content = content
                            self.headers = dict(headers)
                            self.url = url
                        
                        def text(self):
                            return self.content.decode('utf-8')
                        
                        def json(self):
                            import json
                            return json.loads(self.content.decode('utf-8'))
                    logger.info(f"异步GET请求成功: {url}, 状态码: {response.status}")
                    return AsyncResponse(response.status, content, response.headers, str(response.url))
        except Exception as e:
            logger.error(f"异步GET请求失败: {url}, 错误: {str(e)}")
            raise
    
    def close(self):
        self.session.close()

# 创建默认HTTP客户端实例
http_client = HttpClient()
