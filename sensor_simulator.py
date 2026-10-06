"""
Sensor Simulator

Generates realistic sensor data and POSTs to the FastAPI hub.
Run this in a separate terminal alongside the FastAPI app.

Usage:
    python sensor_simulator.py
"""

import time
import json
import random
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import requests

# Configuration
HUB_URL = "http://localhost:8000/api/hub/data"
READ_INTERVAL = 5  # seconds between readings
REQUEST_TIMEOUT = 3  # seconds

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class DHT22Simulator:
    """Simulates a DHT22 temperature/humidity sensor."""
    
    def __init__(self, base_temp: float = 22.0, base_humidity: float = 50.0):
        """
        Initialize DHT22 simulator.
        
        Args:
            base_temp: Starting temperature in Celsius
            base_humidity: Starting humidity percentage
        """
        self.base_temp = base_temp
        self.base_humidity = base_humidity
        self.read_count = 0
        self.temp_drift = 0.0
    
    def read(self) -> Optional[Dict[str, Any]]:
        """
        Simulate a DHT22 reading.
        
        Returns realistic readings with:
        - Gradual temperature drift (random walk)
        - Humidity that changes with temperature
        - ~5% chance of read failure (sensor needs retry)
        """
        self.read_count += 1
        
        # 5% chance of read failure
        if random.random() < 0.05:
            logger.debug("DHT22: Read failure (retry next cycle)")
            return None
        
        # Temperature drift: random walk with small steps
        drift_step = random.gauss(0, 0.15)  # Gaussian random step
        self.temp_drift += drift_step
        self.base_temp += drift_step * 0.05
        
        # Keep temperature in realistic range (-40 to +80°C)
        self.base_temp = max(-40, min(80, self.base_temp))
        
        # Humidity noise: decreases as temperature increases (realistic)
        humidity_noise = random.gauss(0, 1.5)
        self.base_humidity = max(0, min(100, self.base_humidity + humidity_noise))
        
        return {
            "temperature": round(self.base_temp, 1),
            "humidity": round(self.base_humidity, 1),
        }


class PIRSimulator:
    """Simulates a PIR motion sensor."""
    
    def __init__(self, cooldown_seconds: int = 30):
        """
        Initialize PIR simulator.
        
        Args:
            cooldown_seconds: Seconds to wait after motion before detecting again
        """
        self.cooldown = cooldown_seconds
        self.last_motion_time = 0
        self.motion_count = 0
    
    def read(self) -> Dict[str, Any]:
        """
        Simulate a PIR reading.
        
        Returns motion status with:
        - Cooldown period after motion detection
        - ~10% baseline chance of motion (can be manually triggered)
        """
        current_time = time.time()
        
        # Check if still in cooldown period
        if current_time - self.last_motion_time < self.cooldown:
            return {"motion": False}
        
        # 10% chance of detecting motion
        if random.random() < 0.10:
            self.last_motion_time = current_time
            self.motion_count += 1
            logger.info(f"🚨 PIR: Motion detected! (count: {self.motion_count})")
            return {"motion": True}
        
        return {"motion": False}


def send_reading(sensor_id: str, sensor_type: str, data: Dict[str, Any]) -> bool:
    """
    POST a sensor reading to the hub.
    
    Args:
        sensor_id: Sensor identifier (e.g., "dht22_01")
        sensor_type: Sensor type (e.g., "temperature_humidity")
        data: Reading data as dictionary
    
    Returns:
        True if successful, False if failed
    """
    payload = {
        "sensor_id": sensor_id,
        "type": sensor_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    try:
        response = requests.post(
            HUB_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        if response.status_code == 201:
            logger.debug(f"✓ {sensor_id}: {data}")
            return True
        else:
            logger.error(f"✗ {sensor_id}: HTTP {response.status_code} - {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ {sensor_id}: Cannot connect to hub. Is FastAPI running?")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"✗ {sensor_id}: Request timeout")
        return False
    except Exception as e:
        logger.error(f"✗ {sensor_id}: {str(e)}")
        return False


def main():
    """Main loop - read sensors and post to hub."""
    logger.info("=" * 60)
    logger.info("Smart Home Sensor Simulator")
    logger.info("=" * 60)
    logger.info(f"Hub URL: {HUB_URL}")
    logger.info(f"Read interval: {READ_INTERVAL} seconds")
    logger.info("")
    
    # Initialize sensors
    dht22 = DHT22Simulator(base_temp=22.0, base_humidity=50.0)
    pir = PIRSimulator(cooldown_seconds=30)
    
    read_count = 0
    
    try:
        while True:
            read_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            logger.info(f"[{read_count:04d}] {timestamp} - Reading sensors...")
            
            # Read DHT22 (temperature + humidity)
            dht_data = dht22.read()
            if dht_data:
                send_reading("dht22_01", "temperature_humidity", dht_data)
            else:
                logger.warning("⚠️  dht22_01: Read failed")
            
            # Read PIR (motion)
            pir_data = pir.read()
            send_reading("pir_01", "motion", pir_data)
            
            # Wait before next read cycle
            time.sleep(READ_INTERVAL)
    
    except KeyboardInterrupt:
        logger.info("\n🛑 Simulator stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
    finally:
        logger.info("Simulator shut down")


if __name__ == "__main__":
    main()
