import threading
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QRadioButton, QProgressBar,
    QVBoxLayout, QHBoxLayout, QFrame, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from app.services.api_service import api_service
from app.services.download_service import download_service
from app.services.config_service import config_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    update_api_info = pyqtSignal(str)
    update_status = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    show_progress = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("随机Setu下载器")
        self.setGeometry(100, 100, 600, 450)
        self.setFixedSize(600, 450)
        
        self.is_closing = False
        
        self.update_api_info.connect(self._on_update_api_info)
        self.update_status.connect(self._on_update_status)
        self.update_progress.connect(self._on_update_progress)
        self.show_progress.connect(self._on_show_progress)
        
        self._create_ui()
        self._load_config()
        self._init_api_load()
    
    def _load_config(self):
        window_geometry = config_service.get_window_geometry()
        if window_geometry:
            try:
                from PyQt5.QtCore import QByteArray
                self.restoreGeometry(QByteArray(window_geometry))
            except Exception as e:
                logger.error(f"恢复窗口几何信息失败: {str(e)}")
        
        api_source = config_service.get_api_source()
        if api_source == "local":
            self.local_radio.setChecked(True)
        else:
            self.recommended_radio.setChecked(True)
    
    def _create_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        top_frame = QFrame(self)
        top_frame.setStyleSheet("background-color: #f0f0f0")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(20, 20, 20, 20)
        
        self.settings_button = QPushButton("设置API", self)
        self.settings_button.setFont(QFont("微软雅黑", 10))
        self.settings_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 5px 10px; }")
        self.settings_button.clicked.connect(self._open_api_settings)
        top_layout.addWidget(self.settings_button)
        
        top_layout.addStretch(1)
        
        api_source_layout = QHBoxLayout()
        
        self.recommended_radio = QRadioButton("从推荐API获取")
        self.recommended_radio.setStyleSheet("QRadioButton { background-color: #f0f0f0; }")
        self.recommended_radio.clicked.connect(self._on_api_source_change)
        api_source_layout.addWidget(self.recommended_radio)
        
        self.local_radio = QRadioButton("从本地apis.txt获取")
        self.local_radio.setStyleSheet("QRadioButton { background-color: #f0f0f0; }")
        self.local_radio.clicked.connect(self._on_api_source_change)
        api_source_layout.addWidget(self.local_radio)
        
        top_layout.addLayout(api_source_layout)
        
        main_layout.addWidget(top_frame)
        
        content_frame = QFrame(self)
        content_frame.setStyleSheet("QFrame { background-color: #f0f0f0; }")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("随机Setu下载器", self)
        title_label.setFont(QFont("微软雅黑", 20, QFont.Bold))
        title_label.setStyleSheet("QLabel { background-color: #f0f0f0; }")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)
        content_layout.addSpacing(30)
        
        self.download_button = QPushButton("随机下载", self)
        self.download_button.setFont(QFont("微软雅黑", 24, QFont.Bold))
        self.download_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 20px 40px; }")
        self.download_button.clicked.connect(self._start_download)
        content_layout.addWidget(self.download_button, 0, Qt.AlignCenter)
        content_layout.addSpacing(20)
        
        self.status_label = QLabel("点击按钮开始下载", self)
        self.status_label.setFont(QFont("微软雅黑", 12))
        self.status_label.setStyleSheet("QLabel { background-color: #f0f0f0; }")
        self.status_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.status_label)
        content_layout.addSpacing(10)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("QProgressBar { background-color: #e0e0e0; border-radius: 5px; padding: 1px; text-align: center; } QProgressBar::chunk { background-color: #4CAF50; border-radius: 4px; }")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        content_layout.addWidget(self.progress_bar)
        content_layout.addSpacing(10)
        
        self.api_info_label = QLabel("正在加载API...", self)
        self.api_info_label.setFont(QFont("微软雅黑", 10))
        self.api_info_label.setStyleSheet("QLabel { background-color: #f0f0f0; color: #666; }")
        self.api_info_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.api_info_label)
        
        main_layout.addWidget(content_frame)
        main_layout.addStretch(1)
    
    def _on_update_api_info(self, text):
        try:
            self.api_info_label.setText(text)
        except Exception as e:
            logger.error(f"更新API信息标签失败: {str(e)}")
    
    def _on_update_status(self, text):
        try:
            self.status_label.setText(text)
        except Exception as e:
            logger.error(f"更新状态标签失败: {str(e)}")
    
    def _on_update_progress(self, value):
        try:
            self.progress_bar.setValue(value)
        except Exception as e:
            logger.error(f"更新进度条失败: {str(e)}")
    
    def _on_show_progress(self, show):
        try:
            self.progress_bar.setVisible(show)
        except Exception as e:
            logger.error(f"显示/隐藏进度条失败: {str(e)}")
    
    def _init_api_load(self):
        def load_api_task():
            try:
                source = config_service.get_api_source()
                apis = api_service.load_apis(source)
                apis = config_service.load_api_configs(apis)
                
                enabled_count = sum(1 for api in apis if api.enabled)
                total_count = len(apis)
                api_info_text = f"已加载 {total_count} 个API，启用 {enabled_count} 个"
                if source == "local":
                    api_info_text += f"，配置文件: apis.txt"
                else:
                    api_info_text += "，从推荐API获取"
                
                self.update_api_info.emit(api_info_text)
                self._start_preload()
                self.update_status.emit("点击按钮开始下载")
                
            except Exception as e:
                logger.error(f"初始化加载API失败: {str(e)}")
                self.update_status.emit("加载API失败")
        
        init_thread = threading.Thread(target=load_api_task)
        init_thread.daemon = True
        init_thread.start()
    
    def _start_preload(self):
        def preload_task():
            try:
                download_service._preload_images()
                logger.info("预加载完成")
            except Exception as e:
                logger.error(f"预加载失败: {str(e)}")
        
        preload_thread = threading.Thread(target=preload_task)
        preload_thread.daemon = True
        preload_thread.start()
    
    def _start_download(self):
        if self.download_button.text() == "下载中...":
            return
        
        self.download_button.setText("下载中...")
        self.download_button.setStyleSheet("QPushButton { background-color: #45a049; color: white; padding: 20px 40px; }")
        
        def download_task():
            try:
                api_name = download_service.get_random_api_name()
                if not api_name:
                    self.download_button.setText("随机下载")
                    self.download_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 20px 40px; }")
                    self.update_status.emit("没有可用的API")
                    return
                
                animation_running = True
                api_config = api_service.get_api_by_name(api_name)
                api_display_name = api_config.name if api_config else api_name
                
                self.show_progress.emit(True)
                self.update_progress.emit(0)
                
                def download_animation():
                    dots = 0
                    while animation_running and not self.is_closing:
                        try:
                            dots = (dots + 1) % 4
                            animation_text = f"正在从 {api_display_name} 下载{'.' * dots}"
                            self.update_status.emit(animation_text)
                            time.sleep(0.5)
                        except:
                            break
                
                def progress_callback(progress, total_size):
                    try:
                        self.update_progress.emit(progress)
                    except:
                        pass
                
                animation_thread = threading.Thread(target=download_animation)
                animation_thread.daemon = True
                animation_thread.start()
                
                save_path = download_service.download(api_name, progress_callback)
                
                animation_running = False
                
                if save_path:
                    self.update_status.emit(f"下载成功: {save_path.split('/')[-1]}")
                else:
                    self.update_status.emit("下载失败")
                
                self.show_progress.emit(False)
                    
            except Exception as e:
                logger.error(f"下载失败: {str(e)}")
                self.update_status.emit("下载失败")
            finally:
                self.download_button.setText("随机下载")
                self.download_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 20px 40px; }")
                self.show_progress.emit(False)
        
        download_thread = threading.Thread(target=download_task)
        download_thread.daemon = True
        download_thread.start()
    
    def _on_api_source_change(self):
        if self.recommended_radio.isChecked():
            new_source = "recommended"
        else:
            new_source = "local"
        
        config_service.set_api_source(new_source)
        self.update_status.emit("正在加载API...")
        
        def load_api_task():
            try:
                apis = api_service.load_apis(new_source)
                apis = config_service.load_api_configs(apis)
                
                enabled_count = sum(1 for api in apis if api.enabled)
                total_count = len(apis)
                api_info_text = f"已加载 {total_count} 个API，启用 {enabled_count} 个"
                if new_source == "local":
                    api_info_text += f"，配置文件: apis.txt"
                else:
                    api_info_text += "，从推荐API获取"
                
                self.update_api_info.emit(api_info_text)
                self.update_status.emit("点击按钮开始下载")
                self._start_preload()
                
            except Exception as e:
                logger.error(f"加载API失败: {str(e)}")
                self.update_status.emit("加载API失败")
        
        load_thread = threading.Thread(target=load_api_task)
        load_thread.daemon = True
        load_thread.start()
    
    def _open_api_settings(self):
        from app.ui.api_settings_dialog import ApiSettingsDialog
        dialog = ApiSettingsDialog(self)
        dialog.exec_()
    
    def closeEvent(self, event):
        try:
            self.is_closing = True
            
            window_geometry = self.saveGeometry()
            if window_geometry:
                config_service.set_window_geometry(window_geometry.data())
            
            apis = api_service.get_apis()
            config_service.save_api_configs(apis)
            
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
        
        super().closeEvent(event)
