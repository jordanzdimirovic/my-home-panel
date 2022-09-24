# Jordan Zdimirovic
# Device-specific API calls / helpers.

# Currently supports:
# - TP-LINK KASA: Smart Plugs

import binascii
import os
import sys
import threading, asyncio
from asyncio import coroutine
from typing import Coroutine, Dict

from iot_device import SUPPORTED_DEVICE_FAMILIES, discovery_map, status_map, info_map, exec_map

IOT_VALID_DEVICE_FINDS = ["kasaplug", "wizlight"]

def run_coroutine(corr: Coroutine):
    # Get new event loop and call
    asyncio.new_event_loop().run_until_complete(corr)

class IOTDeviceHub():
    def __init__(self, broadcast_ip: str = "255.255.255.255", **enabled_families):
        assert broadcast_ip.endswith(".255"), "IP provided was not a valid broadcast: must end with '.255'"
        
        # What IPs have been associated with corresponding IDs?
        self.ip_id_registry = {}
        
        # What IDs have been associated with corresponding family?
        self.id_fam_registry = {}

        # Python API instances of IOT devices
        self.devices = {}

        # Where / how will IOT devices be discovered?
        self.broadcast_ip = broadcast_ip

        # Is the autofind feature running?
        self.is_autofind_running = False

        # (kwargs) What device families will be discovered?
        self.enabled_families = enabled_families

        # Catalog that gives overview
        self.catalog = {
            # Create empty dict for each valid, provided (truthy) iot device type
            name: [] for name in enabled_families if name in IOT_VALID_DEVICE_FINDS and enabled_families[name]
        }

    
    def start_autofind(self):
        self.is_autofind_running = True
        self._autofind_thread = threading.Thread(target=self._autofind, args=(1, ), daemon=True)
        self._autofind_thread.start()

    def stop_autofind(self):
        self.is_autofind_running = False
        self._autofind_thread.join()

    @staticmethod
    def _generate_new_devid():
        return binascii.b2a_hex(os.urandom(7)).decode().upper()

    def get_devid(self, ip: str):
        if ip in self.ip_id_registry:
            return self.ip_id_registry[ip]

        else:
            self.ip_id_registry[ip] = type(self)._generate_new_devid()
            return self.ip_id_registry[ip]

    def set_family(self, id, family):
        self.id_fam_registry[id] = family

    async def discover_all(self):
        # For every family that is BOTH enabled AND implemented
        for discoverable_family in [family for family in self.enabled_families if family in SUPPORTED_DEVICE_FAMILIES]:
            tmp_catalog = []

            # Call upon the discovery-mapped function    
            lookup_devices = await discovery_map[discoverable_family](self.broadcast_ip)

            # For all looked-up devices
            for device_ip in lookup_devices:
                # Get device
                device = lookup_devices[device_ip]

                # Register / retrieve devid
                devid = self.get_devid(device_ip)

                self.set_family(devid, discoverable_family)

                # Store Python API object
                self.devices[devid] = device
                
                # Get device info (adding ID)
                devinfo = await info_map[discoverable_family](device)
                devinfo["id"] = devid

                # Store info in catalog
                tmp_catalog.append(devinfo)
            
            # Store catalog
            self.catalog[discoverable_family] = tmp_catalog

    async def get_status(self, family, device):
        # Get mapped family and run status
        return await status_map[family](device)

    async def exec_cmd(self, family, device, cmd):
        return await exec_map[family](device, cmd)

    def _autofind(self, poll_rate: int = 1):
        while self.is_autofind_running:
            asyncio.run(self.discover_all())
    

    def get_devices(self):
        return self.catalog
