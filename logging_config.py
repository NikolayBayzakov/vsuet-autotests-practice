import logging
import os
from datetime import datetime

def setup_logging():
    """Настройка логирования для проекта"""
    
    # Создаем папку artifacts если ее нет
    log_dir = "artifacts"
    os.makedirs(log_dir, exist_ok=True)
    
    # Генерируем имя файла с временной меткой
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"run_{timestamp}.log")
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Удаляем существующие обработчики
    logger.handlers.clear()
    
    # Добавляем обработчик для файла
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Добавляем обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger, log_file