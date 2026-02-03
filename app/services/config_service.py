from typing import Optional

from app.config.config_manager import config_manager
from app.models.api import ApiConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ConfigService:
    def __init__(self):
        self.config = config_manager.load()
    
    def load(self) -> dict:
        self.config = config_manager.load()
        logger.info("配置加载成功")
        return self.config
    
    def save(self) -> bool:
        success = config_manager.save(self.config)
        if success:
            logger.info("配置保存成功")
        else:
            logger.error("配置保存失败")
        return success
    
    def get_api_source(self) -> str:
        return self.config.get('api_source', 'recommended')
    
    def set_api_source(self, source: str) -> bool:
        self.config['api_source'] = source
        return self.save()
    
    def get_window_geometry(self) -> Optional[bytes]:
        window_geometry = self.config.get('window_geometry')
        if isinstance(window_geometry, str):
            try:
                import base64
                return base64.b64decode(window_geometry)
            except Exception:
                return None
        return window_geometry
    
    def set_window_geometry(self, geometry: bytes) -> bool:
        self.config['window_geometry'] = geometry
        return self.save()
    
    def save_api_configs(self, api_configs: list[ApiConfig]) -> bool:
        source = self.get_api_source()
        api_dict = {}
        
        for api in api_configs:
            config_key = f"{api.name}_{api.line_number}"
            api_dict[config_key] = {
                'weight': api.weight,
                'params': api.params,
                'enabled': api.enabled,
                'line_number': api.line_number
            }
        
        if source == 'recommended':
            self.config['recommended_apis'] = api_dict
        else:
            self.config['local_apis'] = api_dict
        
        return self.save()
    
    def load_api_configs(self, api_configs: list[ApiConfig]) -> list[ApiConfig]:
        source = self.get_api_source()
        config_key = 'recommended_apis' if source == 'recommended' else 'local_apis'
        saved_configs = self.config.get(config_key, {})
        
        for api in api_configs:
            current_key = f"{api.name}_{api.line_number}"
            if current_key in saved_configs:
                saved_config = saved_configs[current_key]
                api.weight = saved_config.get('weight', api.weight)
                api.params = saved_config.get('params', api.params)
                api.enabled = saved_config.get('enabled', api.enabled)
        
        logger.info(f"加载 {len(api_configs)} 个API配置")
        return api_configs
    
    def get_config(self) -> dict:
        return self.config

# 导出默认配置服务实例
config_service = ConfigService()
