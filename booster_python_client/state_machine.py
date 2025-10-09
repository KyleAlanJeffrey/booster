from enum import Enum
import logging
from typing import Literal

from booster_python_client.types import SpeedType
from . import actions
from .lib import BoosterLowLevelController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("booster_python_client")


class Event:
    """
    An Event is an object that is used to trigger transitions in the state
    machine. Events are processed by the current state, which will then
    determine if a transition should be made.
    """

    def __init__(self, name):
        self.name = name

    def action(self, booster: BoosterLowLevelController, speed: SpeedType):
        """
        The action that is performed when this event is processed.
        """
        pass


class State:
    """
    We define a state object which provides some utility functions for the
    individual states within the state machine.
    """

    def __init__(self):
        print("Processing current state:", str(self))
        self.processed_action = False

    def action(
        self, booster: BoosterLowLevelController, speed: SpeedType, time_gap_s: float
    ):
        """
        The action that is performed when entering the state.
        """
        pass

    def on_event(self, event):
        """
        Handle events that are delegated to this State.
        """
        pass

    def __repr__(self):
        """
        Leverages the __str__ method to describe the State.
        """
        return self.__str__()

    def __str__(self):
        """
        Returns the name of the State.
        """
        return self.__class__.__name__


### EVENTS ###
class RightPunch(Event):
    def __init__(self):
        super().__init__("right_punch")

    def action(
        self, booster: BoosterLowLevelController, speed: SpeedType, time_gap_s: float
    ):
        logger.info("Right Punch!")
        booster.send_command(actions.RIGHT_PUNCH, speed=speed, time_gap_s=time_gap_s)


class LeftPunch(Event):
    def __init__(self):
        super().__init__("left_punch")

    def action(
        self,
        booster: BoosterLowLevelController,
        speed: SpeedType,
        time_gap_s: float,
    ):
        logger.info("Left Punch!")
        booster.send_command(actions.LEFT_PUNCH, speed=speed, time_gap_s=time_gap_s)


class Block(Event):
    def __init__(self):
        super().__init__("block")


### STATES ###
class FightStance(State):
    def action(
        self, booster: BoosterLowLevelController, speed: SpeedType, time_gap_s: float
    ):
        logger.info("Entering fight stance")
        booster.send_command(actions.NEUTRAL_POSE, speed=speed, time_gap_s=time_gap_s)

    def on_event(self, event: Event):
        if event.name == "block":
            return BlockStance()
        elif event.name == "left_punch":
            return self
        if event.name == "right_punch":
            return self


class BlockStance(State):

    def action(
        self, booster: BoosterLowLevelController, speed: SpeedType, time_gap_s: float
    ):
        logger.info("Entering block stance")
        booster.send_command(actions.BLOCK_POSE, speed=speed, time_gap_s=time_gap_s)

    def on_event(self, event: Event):
        if event.name == "block":
            return FightStance()
        elif event.name == "left_punch" or event.name == "right_punch":
            logger.info("Can't punch while blocking!")
            return self


class FightingStateMachine:
    """This state machine works on transitions. So there's nothing running coninuously while in a state."""

    def __init__(
        self,
        booster: BoosterLowLevelController,
        speed: Literal["slow", "medium", "fast"] = "medium",
        time_gap_s: float = 0.05,
    ):
        self.booster = booster
        self.speed = speed
        self.time_gap_s = time_gap_s
        self.state = FightStance()

    def on_event(self, event: Event):
        """
        This is the main event processor which delegates to the current state
        and updates the current state based on the result.
        """
        # Run the events action
        event.action(self.booster, speed=self.speed, time_gap_s=self.time_gap_s)

        # Transition to the next state
        self.state = self.state.on_event(event)

        # Perform the action of the new state
        self.state.action(self.booster, speed=self.speed, time_gap_s=self.time_gap_s)
