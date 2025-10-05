import logging
import signal
import threading

from booster_robotics_sdk_python import (
    B1RemoteControllerStateSubscriber,
    RemoteControllerState,
)

from . import actions
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
                robot.send_command(actions.RIGHT_PUNCH, speed="slow", time_gap_s=0.05)
            elif rc.b:
                robot.send_command(actions.LEFT_PUNCH, speed="slow", time_gap_s=0.05)
            if rc.a:
                robot.send_command(actions.BLOCK, speed="fast", time_gap_s=0.05)
            else:
                robot.send_command(actions.NEUTRAL_POSE, speed="fast", time_gap_s=0.05)

    sub = B1RemoteControllerStateSubscriber(on_remote)
    sub.InitChannel()

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
