"""
Environmental Scanner for Kor'tana.

This module is responsible for perceiving and interpreting the agent's operational environment.
It provides data on system resources, file system changes, and other relevant environmental factors.
"""

import threading
import time

import psutil  # Added psutil import

# We will add watchdog imports later after checking/installing them.

class EnvironmentalScanner:
    """
    Scans the environment for relevant data and makes it available to other agent components.
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.resource_scan_interval = self.config.get("resource_scan_interval_seconds", 5)
        # For disk usage, we'll default to checking the root directory.
        # This could be made configurable if specific mount points are needed.
        self.disk_path_to_monitor = self.config.get("disk_path_to_monitor", "/")
        self.file_system_paths_to_watch = self.config.get("file_system_paths_to_watch", ["."]) # Default to current dir

        self._stop_event = threading.Event()
        self._resource_thread = None
        self._file_watcher_thread = None

        self.system_resources = {}
        self.file_system_events = [] # Store a list of recent events, or use a queue

    def start(self):
        """Starts the environmental scanning threads."""
        print("Starting Environmental Scanner...")
        self._stop_event.clear()

        # Start System Resource Monitoring Thread
        self._resource_thread = threading.Thread(target=self._monitor_system_resources, daemon=True)
        self._resource_thread.start()

        # Start File System Event Detection Thread (to be implemented)
        # self._file_watcher_thread = threading.Thread(target=self._monitor_file_system, daemon=True)
        # self._file_watcher_thread.start()

        print("Environmental Scanner started.")

    def stop(self):
        """Stops the environmental scanning threads."""
        print("Stopping Environmental Scanner...")
        self._stop_event.set()

        if self._resource_thread and self._resource_thread.is_alive():
            self._resource_thread.join()
        # if self._file_watcher_thread and self._file_watcher_thread.is_alive():
        #     self._file_watcher_thread.join()

        print("Environmental Scanner stopped.")

    def _monitor_system_resources(self):
        """Periodically monitors system resources like CPU, RAM, and disk usage using psutil."""
        print("System resource monitoring thread started.")
        while not self._stop_event.is_set():
            try:
                cpu_percent = psutil.cpu_percent(interval=None) # Non-blocking
                memory_info = psutil.virtual_memory()
                disk_info = psutil.disk_usage(self.disk_path_to_monitor)

                self.system_resources = {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_info.percent,
                    "disk_usage_percent": disk_info.percent,
                    "timestamp": time.time()
                }
                # print(f"DEBUG: Scanned resources: {self.system_resources}") # For debugging
            except psutil.Error as e:
                print(f"Error scanning system resources: {e}")
                self.system_resources = { # Report error state
                    "error": str(e),
                    "timestamp": time.time()
                }
            except Exception as e:
                print(f"Unexpected error in resource monitoring: {e}")
                self.system_resources = {
                    "error": f"Unexpected: {str(e)}",
                    "timestamp": time.time()
                }

            # Wait for the scan interval or stop event
            self._stop_event.wait(self.resource_scan_interval)
        print("System resource monitoring thread stopped.")

    def get_system_resources(self):
        """Returns the latest snapshot of system resources."""
        return self.system_resources

    # --- File System Event Detection (to be implemented) ---
    # def _monitor_file_system(self):
    #     """Monitors file system events in specified paths."""
    #     # This method will be populated with watchdog logic
    #     print("File system monitoring thread started.")
    #     # ... watchdog implementation ...
    #     print("File system monitoring thread stopped.")

    # def get_file_system_events(self, limit=10):
    #     """Returns the latest file system events."""
    #     return self.file_system_events[-limit:]


if __name__ == '__main__':
    # Example Usage (for testing purposes)
    scanner_config = {
        "resource_scan_interval_seconds": 3,
        "disk_path_to_monitor": "C:\\", # Monitor C drive on Windows
        "file_system_paths_to_watch": ["c:\\project-kortana\\tests"]
    }
    # On non-Windows, default disk_path_to_monitor might be "/"
    import os
    if os.name != 'nt':
        scanner_config["disk_path_to_monitor"] = "/"

    scanner = EnvironmentalScanner(config=scanner_config)
    scanner.start()

    try:
        for i in range(5): # Run for a short period for testing
            # Wait for a period slightly longer than scan interval to ensure new data
            time.sleep(scanner.resource_scan_interval + 0.5)
            resources = scanner.get_system_resources()
            print(f"Main Thread - Current Resources: {resources}")
            # file_events = scanner.get_file_system_events()
            # if file_events:
            #     print(f"Main Thread - File Events: {file_events}")
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        scanner.stop()
        print("Scanner example finished.")

