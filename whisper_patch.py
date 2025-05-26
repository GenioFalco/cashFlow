"""
Патч для исправления ошибки torch.get_default_device в библиотеке whisper
"""

import torch
import logging

logger = logging.getLogger(__name__)

# Проверяем версию PyTorch
logger.info(f"PyTorch version: {torch.__version__}")

# Добавляем метод get_default_device, если его нет
if not hasattr(torch, 'get_default_device'):
    logger.info("Добавляем метод torch.get_default_device")
    
    def get_default_device():
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    torch.get_default_device = get_default_device
    logger.info(f"Добавлен метод torch.get_default_device, возвращающий: {torch.get_default_device()}") 