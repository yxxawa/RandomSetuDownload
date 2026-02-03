import os
import random
from typing import List, Optional

from app.models.api import ApiConfig
from app.network.http_client import http_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ApiService:
    def __init__(self, api_file: str = "apis.txt", recommended_api_url: str = "https://gitee.com/yxxawa/gg/raw/master/apis.txt"):
        self.api_file = api_file
        self.recommended_api_url = recommended_api_url
        self.apis: List[ApiConfig] = []
        self.recommended_api_cache: Optional[str] = None
    
    def load_apis(self, source: str = "recommended") -> List[ApiConfig]:
        try:
            if source == "recommended":
                apis = self._load_recommended_apis()
            else:
                apis = self._load_local_apis()
            
            self.apis = apis
            logger.info(f"API加载成功，共加载 {len(apis)} 个API")
            return apis
        except Exception as e:
            logger.error(f"API加载失败: {str(e)}")
            return []
    
    def _load_recommended_apis(self) -> List[ApiConfig]:
        try:
            if not self.recommended_api_cache:
                response = http_client.get(self.recommended_api_url)
                self.recommended_api_cache = response.text
            
            return self._parse_api_content(self.recommended_api_cache, "recommended")
        except Exception as e:
            logger.error(f"推荐API加载失败: {str(e)}")
            return []
    
    def _load_local_apis(self) -> List[ApiConfig]:
        try:
            if not os.path.exists(self.api_file):
                with open(self.api_file, 'w', encoding='utf-8') as f:
                    f.write('')
                return []
            
            with open(self.api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._parse_api_content(content, "local")
        except Exception as e:
            logger.error(f"本地API加载失败: {str(e)}")
            return []
    
    def _parse_api_content(self, content: str, source: str) -> List[ApiConfig]:
        apis = []
        total_weight = 0
        actual_line_num = 0
        
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            
            if not line:
                continue
            
            if '#' in line:
                line = line.split('#', 1)[0].strip()
                if not line:
                    continue
            
            actual_line_num += 1
            
            supports_params = False
            if line.startswith('!'):
                supports_params = True
                line = line[1:].strip()
            
            api_name = None
            api_url = line
            
            if ':' in line:
                colon_pos = line.find(':')
                if colon_pos + 2 < len(line) and line[colon_pos+1:colon_pos+3] != '//':
                    api_name_candidate = line[:colon_pos].strip()
                    if api_name_candidate:
                        api_name = api_name_candidate
                        api_url = line[colon_pos+1:].strip()
            
            if api_url.startswith('!'):
                supports_params = True
                api_url = api_url[1:].strip()
            
            weight = 1
            description = ""
            if '{' in api_url and '}' in api_url:
                start_idx = api_url.find('{')
                end_idx = api_url.rfind('}')
                if start_idx < end_idx:
                    description = api_url[start_idx+1:end_idx].strip()
                    api_url = api_url[:start_idx].strip() + api_url[end_idx+1:].strip()
            
            if '|' in api_url:
                parts = api_url.split('|')
                if len(parts) >= 3:
                    try:
                        weight = int(parts[1].strip())
                        api_url = parts[0].strip()
                    except ValueError:
                        pass
            
            if not api_url:
                continue
            
            if not api_name:
                api_name = f"{source}_api_{actual_line_num}"
            
            api_config = ApiConfig(
                name=api_name,
                url=api_url,
                weight=weight,
                description=description,
                enabled=True,
                supports_params=supports_params,
                params="",
                source=source,
                line_number=actual_line_num
            )
            
            apis.append(api_config)
            total_weight += weight
        
        if total_weight > 0:
            for api in apis:
                api.weight = int(api.weight / total_weight * 100)
        elif apis:
            weight_per_api = int(100 / len(apis))
            for api in apis:
                api.weight = weight_per_api
        
        return apis
    
    def get_random_api(self) -> Optional[ApiConfig]:
        try:
            enabled_apis = [api for api in self.apis if api.enabled]
            if not enabled_apis:
                logger.warning("没有启用的API")
                return None
            
            weighted_apis = []
            for api in enabled_apis:
                weighted_apis.extend([api] * api.weight)
            
            if weighted_apis:
                return random.choice(weighted_apis)
            else:
                return random.choice(enabled_apis)
        except Exception as e:
            logger.error(f"随机获取API失败: {str(e)}")
            return None
    
    def update_api(self, api_config: ApiConfig) -> bool:
        try:
            for i, api in enumerate(self.apis):
                if api.name == api_config.name and api.source == api_config.source:
                    self.apis[i] = api_config
                    logger.info(f"API更新成功: {api_config.name}")
                    return True
            
            self.apis.append(api_config)
            logger.info(f"API添加成功: {api_config.name}")
            return True
        except Exception as e:
            logger.error(f"API更新失败: {str(e)}")
            return False
    
    def get_apis(self) -> List[ApiConfig]:
        return self.apis
    
    def get_api_by_name(self, name: str) -> Optional[ApiConfig]:
        for api in self.apis:
            if api.name == name:
                return api
        return None

# 导出默认API服务实例
api_service = ApiService()
