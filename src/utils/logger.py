import logging
import os
from logging.handlers import RotatingFileHandler # Keep for reference if needed

class MaxLinesRotatingFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False, max_lines=100):
        super().__init__(filename, mode, encoding, delay)
        self.max_lines = max_lines
        self.buffer = []

    def emit(self, record):
        # Format the record first
        msg = self.format(record)
        self.buffer.append(msg)

        # If buffer exceeds max_lines, truncate it
        if len(self.buffer) > self.max_lines:
            self.buffer = self.buffer[-self.max_lines:]

        # Write the entire buffer to the file
        # This is inefficient for very large files/buffers, but for 100 lines it's fine.
        self.acquire()
        try:
            with open(self.baseFilename, 'w', encoding=self.encoding) as f:
                for line in self.buffer:
                    f.write(line + self.terminator)
        finally:
            self.release()

def setup_logger(name, log_file, level=logging.INFO, max_lines=100):
    """Function to setup as many loggers as you want"""

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File handler
    handler = MaxLinesRotatingFileHandler(log_file, max_lines=max_lines)
    handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(console_handler)

    return logger

# Create a logger instance
app_logger = setup_logger('LiveTradingApp', 'logs/live_trading.log')
