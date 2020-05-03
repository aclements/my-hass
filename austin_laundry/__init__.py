from .washer import WasherMonitor
from .dryer import DryerMonitor

import logging
import datetime

import homeassistant.helpers.event as event
import homeassistant.const as const

DOMAIN = "austin_laundry"

WASHER_ENTITY = "sensor.zooz_zen15_power_switch_power"
DRYER_ENTITY = "sensor.zooz_zen15_power_switch_power_2"
WASHER_DOOR_ENTITY = "binary_sensor.sensative_strips_sensor"

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    _LOGGER.debug("registering austin_laundry")

    washer = WasherMonitor()
    plumb_state(hass, WASHER_ENTITY, "washer", washer)
    async def async_door_opened(entity_id, old_state, new_state):
        washer.door_opened()
    # The washer door is "off" when closed and "on" when open.
    event.async_track_state_change(hass, WASHER_DOOR_ENTITY, async_door_opened, "off", "on")

    plumb_state(hass, DRYER_ENTITY, "dryer", DryerMonitor())

    # Return boolean to indicate that initialization was successful.
    return True

def plumb_state(hass, entity_id, typ, monitor):
    prev_state = None
    async def async_change(entity_id, old_state, new_state):
        nonlocal prev_state
        _LOGGER.debug("%s power changed %s", typ, new_state)
        power = try_float(new_state.state)
        if new_state.state == const.STATE_UNAVAILABLE:
            state = const.STATE_UNAVAILABLE
        elif power == None:
            _LOGGER.warn("bad %s power %s", typ, new_state.state)
            state = const.STATE_PROBLEM
        else:
            monitor.update(datetime.datetime.now(), power)
            state = monitor.state

        if state != prev_state:
            _LOGGER.debug("new %s state %s", typ, monitor.state)
            hass.states.async_set(
                "austin_laundry."+typ, monitor.state)
            prev_state = monitor.state
    event.async_track_state_change(hass, entity_id, async_change)

def try_float(s):
    try:
        return float(s)
    except ValueError:
        return None
