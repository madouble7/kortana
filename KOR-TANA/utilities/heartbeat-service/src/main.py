import os
import time
import logging
from heartbeat import refresh_token

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Starting Kor'tana Heartbeat Service...")
    
    while True:
        refresh_token()
        logging.info("Kor'tana is awake.")
        time.sleep(60)  # Wait for 60 seconds before the next heartbeat

if __name__ == "__main__":
    main()