import time
from apscheduler.schedulers.background import BackgroundScheduler
from .heartbeat import refresh_token  # Assuming this function exists in heartbeat.py
from .logging import logger  # Assuming logger is set up in logging.py

def start_heartbeat_service():
    scheduler = BackgroundScheduler()
    scheduler.add_job(heartbeat_task, 'interval', seconds=60)  # Adjust the interval as needed
    scheduler.start()
    logger.info("Heartbeat service started.")

def heartbeat_task():
    refresh_token()  # Refresh the token
    logger.info("Kor'tana is awake.")  # Log the message indicating she is awake

# Call start_heartbeat_service() in the main application entry point to initiate the heartbeat service.