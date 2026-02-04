import logging
import os
import datetime

# 日志目录
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 获取当前时间作为日志文件名的一部分
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"{current_time}-log.txt"

# 配置日志
# 创建文件处理器（记录所有级别）
file_handler = logging.FileHandler(os.path.join(LOG_DIR, log_filename))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 创建控制台处理器（只记录错误级别）
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 获取根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# 创建日志记录器
def get_logger(name):
    """获取日志记录器"""
    return logging.getLogger(name)

# 导出默认日志记录器
logger = get_logger(__name__)
