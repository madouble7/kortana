# kortana-heartbeat-service

## Overview
The Kor'tana Heartbeat Service is a lightweight service designed to keep the Kor'tana AI assistant active by refreshing its authentication token at regular intervals. This service logs a message indicating that Kor'tana is awake, ensuring that the assistant remains responsive.

## Features
- Automatic token refresh to maintain session validity.
- Logging to track the service's activity and status.
- Configurable settings for easy customization.

## Project Structure
```
kortana-heartbeat-service
├── src
│   ├── __init__.py
│   ├── main.py          # Entry point for the heartbeat service
│   ├── config.py        # Configuration settings
│   ├── heartbeat.py     # Heartbeat functionality
│   ├── token_manager.py  # Token management
│   ├── utils
│   │   ├── __init__.py
│   │   ├── logging.py    # Logging configuration
│   │   └── scheduler.py   # Scheduling utilities
│   └── tests
│       ├── __init__.py
│       ├── test_heartbeat.py  # Unit tests for heartbeat functionality
│       └── test_token_manager.py  # Unit tests for token management
├── .env.example          # Example environment variables
├── requirements.txt      # Project dependencies
├── pyproject.toml       # Project configuration
└── README.md             # Project documentation
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd kortana-heartbeat-service
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables by copying `.env.example` to `.env` and updating the values as needed.

## Usage
To start the heartbeat service, run:
```
python src/main.py
```

## Logging
The service logs its activity, which can be configured in `src/utils/logging.py`. Ensure that the logging level is set appropriately for your needs.

## Testing
To run the tests, navigate to the `src/tests` directory and execute:
```
pytest
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.