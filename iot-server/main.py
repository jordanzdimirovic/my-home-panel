# Jordan Zdimirovic
# Server for interfacing with smarthome
# IOT devices.

# Flask, used for basic web-server
import asyncio
import sys
from flask import Flask, jsonify, request

# ASYNCIO FIX FOR WINDOWS:
if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

server = Flask(__name__)

from iot_hub import IOTDeviceHub, run_coroutine
from iot_cmd import SUPPORTED_COMMAND_TYPES, SwitchCommand, ensure_params_satisfy


from kasa import SmartPlug as KasaSmartPlug

# Main loop
loop = asyncio.new_event_loop()

# Create finder instance
iot_find = IOTDeviceHub("192.168.1.255", kasaplug=True, wizlight=True)

@server.route("/refresh", methods=["GET"])
def perform_refresh():
    loop.run_until_complete(iot_find.discover_all())
    return "Done.", 200

@server.route("/catalog", methods=["GET"])
def get_catalog():
    return jsonify(iot_find.get_devices()), "200"

@server.route("/status/<device_id>", methods=["GET"])
def get_status(device_id: str):
    if device_id not in iot_find.id_fam_registry:
        return jsonify({"reason": "Device not found or not recognised."}), 404
    
    fam = iot_find.id_fam_registry[device_id]
    dev = iot_find.devices[device_id]
    return jsonify(loop.run_until_complete(iot_find.get_status(fam, dev))), 200

    
@server.route("/control/<cmd_type>/<device_id>", methods=["POST"])
def perform_cmd(cmd_type: str, device_id: str):
    req_data = request.json
    print(req_data)
    if not ensure_params_satisfy(cmd_type, req_data):
        return jsonify({"reason": f"Not all parameters were satisfied for command '{cmd_type}'"})

    if device_id not in iot_find.id_fam_registry:
        return jsonify({"reason": "Device not found or not recognised."}), 404
    
    fam = iot_find.id_fam_registry[device_id]

    if cmd_type not in SUPPORTED_COMMAND_TYPES[fam]:
        return jsonify({"reason": f"Device family {fam} doesn't support command '{cmd_type}'"}), 404

    dev = iot_find.devices[device_id]

    # Determine command
    cmd = None
    
    if cmd_type == "switch":
        # Generate command
        cmd = SwitchCommand(
            state=req_data['state']
        )

    else:
        return jsonify({"reason": f"Command '{cmd_type}' not found"}), 400

    return jsonify(loop.run_until_complete(iot_find.exec_cmd(fam, dev, cmd))), 200


# Run refresh once
perform_refresh()

#@server.route("/control/")

server.run(host="0.0.0.0", port=12345)
