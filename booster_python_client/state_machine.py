from enum import Enum
import logging
from typing import Dict, List

from .types import SpeedType
from . import actions
from .lib import BoosterLowLevelController
from booster_robotics_sdk_python import B1JointIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("booster_python_client")


class RobotEvent(Enum):
    LEFT_PUNCH = "left_punch"
    RIGHT_PUNCH = "right_punch"
    RIGHT_UPPERCUT = "right_uppercut"
    BLOCK = "block"
    VICTORY_POSE = "victory_pose"


class RobotState(Enum):
    FIGHT_STANCE = "fight_stance"
    BLOCK_STANCE = "block_stance"


class FightingStateMachine:
    """This state machine works on transitions. So there's nothing running coninuously while in a state."""

    def __init__(
        self,
        booster: BoosterLowLevelController,
        speed: SpeedType = "medium",
        time_gap_s: float = 0.05,
    ):
        self.booster = booster
        self.speed = speed
        self.time_gap_s = time_gap_s
        self.state = RobotState.FIGHT_STANCE

    def _action(self, action: List[Dict[B1JointIndex, float]], speed: SpeedType = None, time_gap_s: float = None):
        if speed and time_gap_s:
            self.booster.send_command(action, speed=speed, time_gap_s=time_gap_s)
            return
        self.booster.send_command(action, speed=self.speed, time_gap_s=self.time_gap_s)

    def on_event(self, event: RobotEvent):

        ######### Fighting state #########
        if self.state == RobotState.FIGHT_STANCE:
            # Switch to block stance
            if event == RobotEvent.BLOCK:
                self._action(actions.FIGHT_POSE_TO_BLOCK)
                self.state = RobotState.BLOCK_STANCE

            elif event == RobotEvent.LEFT_PUNCH:
                self._action(actions.LEFT_PUNCH)

            elif event == RobotEvent.RIGHT_PUNCH:
                self._action(actions.RIGHT_PUNCH)

            elif event == RobotEvent.RIGHT_UPPERCUT:
                self._action(actions.RIGHT_UPPERCUT)
            elif event == RobotEvent.VICTORY_POSE:
                self._action(actions.VICTORY_ANIMATION, "slow", .2)
            else:
                logger.info(f"Cant {event.value} while fighting!")

        ######### Blocking state #########
        elif self.state == RobotState.BLOCK_STANCE:
            # Switch back to fight stance
            if event == RobotEvent.BLOCK:
                self._action(actions.BLOCK_TO_FIGHT_POSE)
                self.state = RobotState.FIGHT_STANCE
            elif event == RobotEvent.VICTORY_POSE:
                self._action(actions.VICTORY_ANIMATION)
            else:
                logger.info(f"Can't {event.value} while blocking!")
