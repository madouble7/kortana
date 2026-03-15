"""
Tabby Local AI Service - Ghost Protocol Phase 2 Infrastructure

This service manages the lifecycle of the Tabby ML server and StarCoder-2-7B models.
Part of the Kor'tana Autonomous Development Engine (ADE).
"""

import asyncio
import logging
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class TabbyService:
    """
    Manages the Tabby ML inference server and model provisioning.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.tabby_path = Path(self.config.get("TABBY_EXECUTABLE", "tabby"))
        self.model_id = self.config.get("TABBY_MODEL_ID", "StarCoder2-7B")
        self.port = self.config.get("TABBY_PORT", 8080)
        self.process: Optional[subprocess.Popen] = None
        self._is_active = False

    async def check_availability(self) -> bool:
        """Checks if the Tabby executable is available in the path."""
        try:
            # Check if tabby is in path
            subprocess.run([str(self.tabby_path), "--version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    async def provision_model(self, force: bool = False) -> bool:
        """
        Downloads the StarCoder-2-7B model using Tabby's download logic.
        """
        logger.info(f"Ghost Protocol: Provisioning model {self.model_id}...")
        try:
            # tabby download --model <MODEL_ID>
            cmd = [str(self.tabby_path), "download", "--model", self.model_id]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Model {self.model_id} provisioned successfully.")
                return True
            else:
                logger.error(f"Failed to provision model: {stderr.decode()}")
                return False
        except Exception as e:
            logger.error(f"Error during model provisioning: {e}")
            return False

    async def start_server(self) -> bool:
        """
        Starts the Tabby ML server in the background.
        """
        if self._is_active:
            return True

        logger.info(f"Starting Tabby server on port {self.port}...")
        try:
            # tabby serve --model <MODEL_ID> --port <PORT>
            cmd = [
                str(self.tabby_path), "serve", 
                "--model", self.model_id, 
                "--port", str(self.port),
                "--device", self.config.get("TABBY_DEVICE", "cpu")
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            self._is_active = True
            return True
        except Exception as e:
            logger.error(f"Failed to start Tabby server: {e}")
            return False

    async def stop_server(self) -> bool:
        """Stops the Tabby server process."""
        if self.process:
            self.process.terminate()
            self.process = None
            self._is_active = False
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Returns the current status of the Tabby service."""
        return {
            "active": self._is_active,
            "model_id": self.model_id,
            "port": self.port,
            "pid": self.process.pid if self.process else None
        }
