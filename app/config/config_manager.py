import json
import os
import tempfile

from app.utils.logger import get_logger

logger = get_logger(__name__)

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.default_config = {
            'window_geometry': None,
            'recommended_apis': {},
            'local_apis': {},
            'api_source': 'recommended'
        }
    
    def load(self):
        if not os.path.exists(self.config_file):
            logger.info(f"配置文件不存在，使用默认配置: {self.config_file}")
            return self.default_config.copy()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"配置文件加载成功: {self.config_file}")
                
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                
                return config
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {str(e)}")
            return self.default_config.copy()
        except Exception as e:
            logger.error(f"配置文件加载失败: {str(e)}")
            return self.default_config.copy()
    
    def save(self, config):
        try:
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            self._ensure_serializable(config)
            
            temp_file = tempfile.mktemp()
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            os.replace(temp_file, self.config_file)
            logger.info(f"配置文件保存成功: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"配置文件保存失败: {str(e)}")
            try:
                if 'temp_file' in locals() and os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
            return False
    
    def _ensure_serializable(self, config):
        if 'window_geometry' in config and config['window_geometry'] is not None:
            if isinstance(config['window_geometry'], bytes):
                try:
                    import base64
                    config['window_geometry'] = base64.b64encode(config['window_geometry']).decode('utf-8')
                except Exception:
                    config['window_geometry'] = None

# 导出默认配置管理器
config_manager = ConfigManager('config.json')
