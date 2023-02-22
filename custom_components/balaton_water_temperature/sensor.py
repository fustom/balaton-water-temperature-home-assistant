"""Support for getting the Balatonlelle water temperature."""
from __future__ import annotations

import logging
import aiohttp
import re
import ast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import TEMP_CELSIUS

_LOGGER = logging.getLogger(__name__)

PATH = "https://www.idokep.hu/terkep/hu/vizho.js"
REFERER = "https://www.idokep.hu/hoterkep/balaton"
PLACE = "Balatonlelle"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    async_add_entities([BalatonWaterTemperature(PLACE)])


class BalatonWaterTemperature(SensorEntity):
    """Representation of a sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, place):
        """Initialize a sensor."""
        self.place = place
        self._attr_name = f"{self.place} water temperature"
        self._attr_unique_id = f"{self.place}WaterTemperature"

    async def async_update(self):
        """Get the latest data."""
        self._attr_native_value = await self.__async_request()

    async def __async_request(
        self,
        path: str = PATH,
        method: str = "GET",
    ) -> int:
        """Async request with aiohttp"""
        headers = {"referer": REFERER}

        async with aiohttp.ClientSession() as session:
            response = await session.request(method, path, headers=headers)

            if not response.ok:
                raise Exception(response.status)

            coded_content = await response.content.read()
            content = coded_content.decode()
            content_list = re.search(r"\[\[.*\]\]", content, re.S).group()
            temp_list = ast.literal_eval(content_list)

            return [(temp[2]) for temp in temp_list if temp[3] == self.place][0]
