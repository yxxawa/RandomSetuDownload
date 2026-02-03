from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QLineEdit,
    QPushButton, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QCursor

from app.services.api_service import api_service
from app.services.config_service import config_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ApiSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API设置")
        self.resize(400, 400)
        self.setModal(True)
        
        self._create_ui()
    
    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        self.checkboxes = {}
        self.param_inputs = {}
        
        apis = api_service.get_apis()
        for api in apis:
            api_layout = QHBoxLayout()
            api_layout.setAlignment(Qt.AlignLeft)
            
            checkbox = QCheckBox()
            checkbox.setChecked(api.enabled)
            checkbox.setStyleSheet("background-color: #f0f0f0")
            checkbox.setMinimumSize(20, 20)
            checkbox.setMaximumSize(20, 20)
            api_layout.addWidget(checkbox)
            api_layout.addSpacing(8)
            
            display_text = api.name
            if api.description:
                display_text += f" ({api.description})"
            label = QLabel(display_text)
            label.setStyleSheet("background-color: #f0f0f0")
            label.setFont(QFont("微软雅黑", 11))
            label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            label.setCursor(QCursor(Qt.PointingHandCursor))
            label.mousePressEvent = lambda event, cb=checkbox: cb.setChecked(not cb.isChecked())
            api_layout.addWidget(label)
            api_layout.addStretch(1)
            
            scroll_layout.addLayout(api_layout)
            
            self.checkboxes[api.name] = checkbox
            
            if api.supports_params:
                param_layout = QHBoxLayout()
                param_layout.setContentsMargins(30, 5, 10, 15)
                
                param_label = QLabel("参数:")
                param_label.setStyleSheet("background-color: #f0f0f0")
                param_label.setFont(QFont("微软雅黑", 10))
                param_layout.addWidget(param_label)
                param_layout.addSpacing(8)
                
                param_input = QLineEdit()
                param_input.setText(api.params)
                param_input.setPlaceholderText("例如: tag=萝莉|少女&tag=白丝|黑丝")
                param_input.setFont(QFont("微软雅黑", 10))
                param_input.setStyleSheet("background-color: white; padding: 3px 5px")
                param_layout.addWidget(param_input, 1)
                
                scroll_layout.addLayout(param_layout)
                
                self.param_inputs[api.name] = param_input
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        save_button = QPushButton("保存")
        save_button.setFont(QFont("微软雅黑", 10))
        save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px 20px")
        save_button.clicked.connect(self._save_settings)
        main_layout.addWidget(save_button)
    
    def _save_settings(self):
        try:
            apis = api_service.get_apis()
            
            for api in apis:
                if api.name in self.checkboxes:
                    api.enabled = self.checkboxes[api.name].isChecked()
                
                if api.name in self.param_inputs:
                    api.params = self.param_inputs[api.name].text().strip()
            
            config_service.save_api_configs(apis)
            logger.info("API配置保存成功")
            
            # 清空预加载池，确保下次下载使用新的API参数
            from app.services.download_service import download_service
            with download_service.lock:
                download_service.preload_pool.clear()
            logger.info("预加载池已清空")
            
            self.accept()
            
        except Exception as e:
            logger.error(f"保存API配置失败: {str(e)}")
