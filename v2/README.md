# GPS to MQTT Application

## Overview

This application reads data from GPSD and sends it to an MQTT broker. The current implementation is located in the `v2` folder.

## Prerequisites

Ensure you have the following installed:
- Python 3.7+
- pip (Python package installer)
- Docker
- GPSD (GPS Daemon)
- MQTT Broker (e.g., Mosquitto)

## Installation

1. Clone the repository:
    ```bash
    git clone <repository-url>
    cd gps2mqtt-dev/v2
    ```

2. Set up a virtual environment (optional but recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1. Create a `config.json` file in the `v2` directory with the following structure:
    ```json
    {
        "sleep_interval": 1,
        "mqtt_topics": {
            "state": "gps_module/{combined_id}/state",
            "attributes": "gps_module/{combined_id}/attributes",
            "homeassistant_status": "homeassistant/status"
        }
    }
    ```

2. Update the `settings.py` file with your MQTT broker details.

## Running the Application

1. Ensure GPSD is running and accessible:
    ```bash
    sudo systemctl start gpsd
    sudo systemctl enable gpsd
    ```

2. Run the application:
    ```bash
    python app.py
    ```

## Using the Makefile

The `Makefile` provides convenient targets for building and running the application using Docker.

1. **Build the Docker image**:
    ```bash
    make build
    ```

2. **Run the Docker container**:
    ```bash
    make run
    ```

3. **Stop the Docker container**:
    ```bash
    make stop
    ```

## Debugging

1. **Logging**: The application uses Python's logging module. Logs are output to the console with timestamps, log levels, and messages.
    - To change the log level, modify the `logging.basicConfig` line in `app.py`.

2. **Signal Handling**: The application handles SIGINT and SIGTERM signals to ensure a graceful shutdown. This includes disconnecting from the MQTT brokers and stopping the MQTT loops.

3. **Common Issues**:
    - **GPSD Connection**: Ensure GPSD is running and that the application can connect to it.
    - **MQTT Broker Connection**: Verify the MQTT broker details in `settings.py` and ensure the broker is running.
    - **Configuration Errors**: Ensure `config.json` is correctly formatted and contains all necessary fields.

## Unit Tests

Add unit tests to ensure the correctness of the application logic. You can use `unittest` or `pytest` frameworks for writing tests.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Acknowledgments

- [GPSD](http://catb.org/gpsd/)
- [Paho MQTT](https://www.eclipse.org/paho/index.php?page=clients/python/index.php)
- [Home Assistant](https://www.home-assistant.io/)

---

Feel free to reach out with any questions or issues.
