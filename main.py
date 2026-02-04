import sys
from app.ui.main_window import MainWindow
from app.utils.logger import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    try:
        logger.info("应用启动")
        
        # 创建应用实例
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 启动事件循环
        logger.info("应用启动成功")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 尝试显示错误消息
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(None, "错误", f"应用启动失败: {str(e)}")
        except Exception as e2:
            logger.error(f"显示错误消息失败: {str(e2)}")
            pass
        
    finally:
        # 关闭HTTP客户端会话，释放资源
        try:
            from app.network.http_client import http_client
            http_client.close()
            logger.info("HTTP客户端会话已关闭")
        except Exception as e:
            logger.error(f"关闭HTTP客户端会话失败: {str(e)}")
        
        sys.exit(1 if 'e' in locals() else 0)
