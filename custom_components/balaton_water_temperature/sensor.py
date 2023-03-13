"""Support for getting the Balatonlelle water temperature."""
from __future__ import annotations

from datetime import timedelta
from typing import Final

import logging
import aiohttp
import re
import ast
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as BASE_PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_NAME, UnitOfTemperature
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

PATH = "https://www.idokep.hu/terkep/hu/vizho.js"
REFERER = "https://www.idokep.hu/hoterkep/balaton"
DEFAULT_NAME = "Balatonlelle"

PLATFORM_SCHEMA: Final = BASE_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    name = config[CONF_NAME]
    async_add_entities([BalatonWaterTemperature(name)])


class BalatonWaterTemperature(SensorEntity):
    """Representation of a sensor."""

    def __init__(self, place) -> None:
        """Initialize a sensor."""
        self.place = place

    @property
    def unique_id(self) -> str | None:
        return f"{self.place}WaterTemperature"

    @property
    def name(self) -> str | None:
        return f"{self.place} water temperature"

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self) -> str | None:
        return UnitOfTemperature.CELSIUS

    @property
    def state_class(self) -> SensorStateClass | str | None:
        return SensorStateClass.MEASUREMENT

    @Throttle(timedelta(minutes=5))
    async def async_update(self):
        """Get the latest data."""
        self._attr_native_value = await self.__async_request()

    async def __async_request(
        self,
        path: str = PATH,
        method: str = aiohttp.hdrs.METH_GET,
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

            return next(iter((temp[2]) for temp in temp_list if temp[3] == self.place))
