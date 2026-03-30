import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def log_heartbeat():
    logging.info("Kor'tana is awake and the heartbeat service is running.")