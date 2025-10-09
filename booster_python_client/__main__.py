import argparse
import logging
import signal
import threading

from booster_robotics_sdk_python import (
    B1RemoteControllerStateSubscriber,
    RemoteControllerState,
)

from .state_machine import FightingStateMachine, RobotEvent
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
    parser = argparse.ArgumentParser(description="Fight Mode FSM Controller")
    parser.add_argument(
        "--speed",
        type=str,
        default="medium",
        help="Motion speed setting (slow, medium, fast)",
    )

    args = parser.parse_args()
    logger.info(f"Using speed setting: {args.speed}")
    if args.speed not in ("slow", "medium", "fast"):
        raise ValueError("Invalid speed setting")

    robot = BoosterLowLevelController()
    robot.init(network_interface="")
    # robot.enable_arm_usage()
    fight_sm = FightingStateMachine(robot, speed=args.speed, time_gap_s=0.05)

    def on_remote(rc: RemoteControllerState):
        ev = rc.event
        if ev == EVENT_BTN_DN:
            if rc.rt:
                fight_sm.on_event(RobotEvent.RIGHT_PUNCH)
            elif rc.rb:
                fight_sm.on_event(RobotEvent.RIGHT_UPPERCUT)
            elif rc.lt:
                fight_sm.on_event(RobotEvent.LEFT_PUNCH)
            elif rc.a:
                fight_sm.on_event(RobotEvent.BLOCK)
            elif rc.b:
                fight_sm.on_event(RobotEvent.VICTORY_POSE)

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
