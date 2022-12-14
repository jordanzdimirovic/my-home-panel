import asyncio
from typing import Dict

import kasa
from kasa import Discover, DeviceType as KasaDeviceType

from pywizlight import discovery as wiz_discovery, wizlight

from iot_cmd import IOTCommand, SwitchCommand

# Device-specific discovery functions

#region TP-LINK KASA plugs

async def discover_kasaplug(broadcast_ip: str) -> Dict[str, KasaDeviceType]:
    kasa_all = await Discover.discover(target=broadcast_ip)

    # Filter / return only plugs
    return {
        kasa_ip: kasa_dev for kasa_ip, kasa_dev in kasa_all.items()
        if kasa_dev.device_type == KasaDeviceType.Plug
    }

async def info_kasaplug(kasa_dev: kasa.SmartPlug):
    # Get name, ip and MAC addr
    return {
        "name": kasa_dev.alias,
        "ip": kasa_dev.host,
        "mac": kasa_dev.mac
    }

async def status_kasaplug(kasa_dev: kasa.SmartPlug):
    # First, update
    await kasa_dev.update()

    # Then, return object with status info
    return {
        "status": "ON" if kasa_dev.is_on else "OFF",
        "power_now": await kasa_dev.get_emeter_realtime(),
        "power_today": await kasa_dev.get_emeter_daily()
    }

async def exec_kasaplug(kasa_dev: kasa.SmartPlug, iot_cmd: IOTCommand):
    if type(iot_cmd) is SwitchCommand:
        try:
            if iot_cmd.state:
                await kasa_dev.turn_on()
            else:
                await kasa_dev.turn_off()

        except: pass

    else:
        raise ValueError(f"Kasa plug doesn't support command type: '{type(iot_cmd)}'")

#endregion

#region WIZ SMART LIGHTBULBS

async def discover_wizlight(broadcast_ip: str):
    # Find all wizlights
    print("Discovering wizlights...")
    wizlight_lst = await wiz_discovery.discover_lights(broadcast_space=broadcast_ip)
    
    # Use IP as key
    return {light_obj.ip: light_obj for light_obj in wizlight_lst}

async def info_wizlight(dev: wizlight):
    # Get info
    print("Getting wizlight info...")
    return {
        "ip": dev.ip,
        "mac": await dev.getMac()
    }

async def status_wizlight(dev: wizlight):
    # Perform update
    devstate = await dev.updateState()

    # Get colours
    col = devstate.get_rgb()

    return {
        "status": "ON" if devstate.get_state() else "OFF",
        "brightness": devstate.get_brightness() / 255,
        "colour_preset": devstate.get_colortemp(),
        "colour": {
            "r": col[0],
            "g": col[1],
            "b": col[2]
        }
    }

#endregion

SUPPORTED_DEVICE_FAMILIES = ("kasaplug", "wizlight")

# Dicts (intended to be imported)
discovery_map = {
    "kasaplug": discover_kasaplug,
    "wizlight": discover_wizlight
}

info_map = {
    "kasaplug": info_kasaplug,
    "wizlight": info_wizlight
}

status_map = {
    "kasaplug": status_kasaplug,
    "wizlight": status_wizlight
}

exec_map = {
    "kasaplug": exec_kasaplug
}

# ENSURE ALL IMPLEMENTED
if not all([all([family in map for family in SUPPORTED_DEVICE_FAMILIES]) for map in [discovery_map, info_map, status_map, exec_map]]):
    print("Warning: not all supported devices are implemented")
