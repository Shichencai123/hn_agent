"""Channel service: lifecycle management."""
from __future__ import annotations
import logging
from enum import Enum
from app.channels.manager import ChannelManager
from app.channels.message_bus import MessageBus

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class HealthCheckResult:
    def __init__(self, healthy, status, details=None):
        self.healthy = healthy
        self.status = status
        self.details = details or {}


class ChannelService:
    def __init__(self, manager=None, message_bus=None):
        self._message_bus = message_bus or MessageBus()
        self._manager = manager or ChannelManager(message_bus=self._message_bus)
        self._status = ServiceStatus.STOPPED

    @property
    def status(self):
        return self._status

    @property
    def manager(self):
        return self._manager

    @property
    def message_bus(self):
        return self._message_bus

    async def start(self):
        if self._status == ServiceStatus.RUNNING:
            return
        self._status = ServiceStatus.STARTING
        try:
            await self._message_bus.start()
            self._status = ServiceStatus.RUNNING
        except Exception:
            self._status = ServiceStatus.ERROR
            raise

    async def stop(self):
        if self._status == ServiceStatus.STOPPED:
            return
        self._status = ServiceStatus.STOPPING
        try:
            await self._message_bus.stop()
            self._status = ServiceStatus.STOPPED
        except Exception:
            self._status = ServiceStatus.ERROR
            raise

    def health_check(self):
        channels = self._manager.registered_channels
        return HealthCheckResult(
            healthy=self._status == ServiceStatus.RUNNING,
            status=self._status,
            details={"registered_channels": channels, "channel_count": len(channels)},
        )
