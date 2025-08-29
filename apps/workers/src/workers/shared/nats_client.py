"""
NATS client for inter-service communication.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional

try:
    import nats
    from nats.aio.client import Client as NATS
    HAS_NATS = True
except ImportError:
    HAS_NATS = False
    logging.warning("NATS client not available")

logger = logging.getLogger(__name__)


class NATSClient:
    """NATS client wrapper."""
    
    def __init__(self, nats_url: str):
        self.nats_url = nats_url
        self.nc: Optional[NATS] = None
        self.subscriptions = {}
    
    async def connect(self):
        """Connect to NATS server."""
        if not HAS_NATS:
            logger.warning("NATS not available, using mock client")
            return
        
        try:
            self.nc = await nats.connect(self.nats_url)
            logger.info(f"Connected to NATS at {self.nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {str(e)}")
            raise e
    
    async def disconnect(self):
        """Disconnect from NATS server."""
        if self.nc:
            await self.nc.close()
            logger.info("Disconnected from NATS")
    
    async def publish(self, subject: str, data: Dict[str, Any]):
        """Publish a message to a subject."""
        if not self.nc:
            logger.warning(f"NATS not connected, skipping publish to {subject}")
            return
        
        try:
            message = json.dumps(data).encode()
            await self.nc.publish(subject, message)
            logger.debug(f"Published message to {subject}")
        except Exception as e:
            logger.error(f"Error publishing to {subject}: {str(e)}")
            raise e
    
    async def subscribe(self, subject: str, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to a subject with a callback."""
        if not self.nc:
            logger.warning(f"NATS not connected, skipping subscription to {subject}")
            return
        
        try:
            async def message_handler(msg):
                try:
                    data = json.loads(msg.data.decode())
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error handling message from {subject}: {str(e)}")
            
            sub = await self.nc.subscribe(subject, cb=message_handler)
            self.subscriptions[subject] = sub
            logger.info(f"Subscribed to {subject}")
            
        except Exception as e:
            logger.error(f"Error subscribing to {subject}: {str(e)}")
            raise e
    
    async def request(self, subject: str, data: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        """Send a request and wait for response."""
        if not self.nc:
            logger.warning(f"NATS not connected, skipping request to {subject}")
            return {}
        
        try:
            message = json.dumps(data).encode()
            response = await self.nc.request(subject, message, timeout=timeout)
            return json.loads(response.data.decode())
        except Exception as e:
            logger.error(f"Error making request to {subject}: {str(e)}")
            raise e
    
    async def unsubscribe(self, subject: str):
        """Unsubscribe from a subject."""
        if subject in self.subscriptions:
            await self.subscriptions[subject].unsubscribe()
            del self.subscriptions[subject]
            logger.info(f"Unsubscribed from {subject}")


# Global NATS client instance
_nats_client: Optional[NATSClient] = None


async def get_nats_client() -> NATSClient:
    """Get NATS client instance."""
    global _nats_client
    
    if _nats_client is None:
        from .config import get_settings
        settings = get_settings()
        _nats_client = NATSClient(settings.nats_url)
        await _nats_client.connect()
    
    return _nats_client
