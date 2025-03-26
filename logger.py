import logging
# Файл конфигурации
logger = logging.getLogger("telegram_bot")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log', mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

logger.info("👀 Логгер запущен!")
