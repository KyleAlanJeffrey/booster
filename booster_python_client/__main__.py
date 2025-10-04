import logging
import signal
import threading

from booster_robotics_sdk_python import (
    B1RemoteControllerStateSubscriber,
    RemoteControllerState,
)

from .actions import RIGHT_PUNCH, LEFT_PUNCH
from .lib import BoosterLowLevelController


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("booster_python_client")

EVENT_AXIS, EVENT_HAT, EVENT_BTN_DN, EVENT_BTN_UP, EVENT_REMOVE = (
    0x600,
    0x602,
    0x603,
    0x604,
    0x606,
)

if __name__ == "__main__":
    robot = BoosterLowLevelController()
    robot.init(network_interface="")

    robot.enable_arm_usage()

    def on_remote(rc: RemoteControllerState):
        ev = rc.event
        if ev == EVENT_BTN_DN:
            if rc.x:
                robot.send_command(RIGHT_PUNCH, speed="slow", time_gap_s=0.05)
            if rc.y:
                robot.send_command(LEFT_PUNCH, speed="slow", time_gap_s=0.05)

    sub = B1RemoteControllerStateSubscriber(on_remote)
    sub.InitChannel()
    logger.info("Subscribed: %s", sub.GetChannelName())

    # --- clean, signal-friendly blocker ---
    stop = threading.Event()

    def _handle_stop(signum, frame):
        stop.set()

    # Handle Ctrl-C and kill
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    try:
        # Block here until a stop signal arrives
        stop.wait()  # no busy loop, no CPU burn
    finally:
        # Always clean up no matter how we exit
        try:
            sub.close()
        except Exception as e:
            logger.error("Close error:", e)
        logger.info("Stopping")
