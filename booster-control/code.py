import signal, time
import booster_robotics_sdk_python as br

# pip install the wheel that exposes: booster_robotics_sdk_python
from time import sleep, perf_counter

from booster_robotics_sdk_python import (
    ChannelFactory,
    B1LowStateSubscriber,
    B1LowCmdPublisher,
    LowCmd,
    MotorCmd,
    LowCmdType,
    B1LocoClient,
    RobotMode,
    B1JointIndex as J,  # enums provided in your binding
)

EVENT_AXIS, EVENT_HAT, EVENT_BTN_DN, EVENT_BTN_UP, EVENT_REMOVE = (
    0x600,
    0x602,
    0x603,
    0x604,
    0x606,
)


def on_remote(rc: br.RemoteControllerState):
    ev = rc.event
    # if ev == EVENT_AXIS:
    #     print(f"AXIS lx={rc.lx:+.2f} ly={rc.ly:+.2f} rx={rc.rx:+.2f} ry={rc.ry:+.2f}")
    # elif ev in (EVENT_BTN_DN, EVENT_BTN_UP):
    #     names = [n for n in ("a","b","x","y","lb","rb","lt","rt","ls","rs","back","start")
    #              if getattr(rc, n)]
    #     print(("BTN_DOWN" if ev==EVENT_BTN_DN else "BTN_UP"), names)
    # elif ev == EVENT_HAT:
    #     hats = [n for n in ("hat_c","hat_u","hat_d","hat_l","hat_r","hat_lu","hat_ld","hat_ru","hat_rd")
    #             if getattr(rc, n)]
    #     print("HAT", hats)
    # elif ev == EVENT_REMOVE:
    #     print("CONTROLLER REMOVED")

    if ev == EVENT_BTN_DN:
        if rc.x:
            print("PUNCH!!!")
            punch()


def main():
    br.ChannelFactory.Instance().Init(domain_id=0, network_interface="")
    sub = br.B1RemoteControllerStateSubscriber(on_remote)
    sub.InitChannel()
    print("Subscribed:", sub.GetChannelName())

    try:
        signal.pause()
    except KeyboardInterrupt:
        pass
    finally:
        sub.CloseChannel()


# pip install the wheel that exposes: booster_robotics_sdk_python
from time import sleep, perf_counter

from booster_robotics_sdk_python import (
    ChannelFactory,
    B1LowStateSubscriber,
    B1LowCmdPublisher,
    LowCmd,
    MotorCmd,
    LowCmdType,
    B1LocoClient,
    RobotMode,
    B1JointIndex as J,  # enums provided in your binding
)

# ---- 1) Bring up DDS and switch to Custom mode (so low-level cmds are accepted)
ChannelFactory.Instance().Init(domain_id=0)  # set your domain/interface as needed

loco = B1LocoClient()
loco.Init()
# ret = loco.ChangeMode(RobotMode.kCustom)
# if ret != 0:
#     raise RuntimeError("ChangeMode(kCustom) failed")

# ---- 2) Read ONE LowState to learn SERIAL motor count and current poses
latest_low_state = {"msg": None}


def _grab_once(ls):
    latest_low_state["msg"] = ls


sub = B1LowStateSubscriber(handler=_grab_once)
sub.InitChannel()

# wait up to ~1s to get one packet
for _ in range(100):
    if latest_low_state["msg"] is not None:
        break
    sleep(0.01)

if latest_low_state["msg"] is None:
    raise RuntimeError("Did not receive LowState; check channels / domain / wiring")

low_state = latest_low_state["msg"]
serial_states = low_state.motor_state_serial  # list[MotorState]
serial_cnt = len(serial_states)
parallel_cnt = len(low_state.motor_state_parallel)
print(f"serial motors: {serial_cnt}, parallel motors: {parallel_cnt}")


# ---- 3) Prepare a helper to build a neutral MotorCmd array from current state
def neutral_cmds_from(low_state_list):
    cmds = []
    for s in low_state_list:
        mc = MotorCmd()
        mc.mode = 0  # leave as 0 if your firmware ignores it in PD+weight mode
        mc.q = s.q  # hold current position by default
        mc.dq = 0.0
        mc.tau = 0.0
        mc.kp = 0.0
        mc.kd = 0.0
        mc.weight = 0.0  # weight==0 → joint ignored; >0 → joint considered
        cmds.append(mc)
    return cmds


# ---- 4) Choose which SERIAL joints are the arm (LEFT or RIGHT) and set a punch profile
# Adjust these to your wiring/order if needed. The enum gives semantic names.
ARM_JOINTS_RIGHT = [
    J.kRightShoulderPitch,  # forward/back
    J.kRightShoulderRoll,  # lateral
    J.kRightElbowPitch,  # extend/flex
    J.kRightElbowYaw,  # optional; include if you want pronation/supination
]


# PD gains for a snappy but controlled hit — start modest!
KP_HARD = 80.0
KP_MED = 40.0
KP_LOW = 20.0
KD_MED = 2.0

# ---- 5) Build publisher
pub = B1LowCmdPublisher()
pub.InitChannel()


def send_serial_cmds(cmds):
    msg = LowCmd()
    msg.cmd_type = LowCmdType.SERIAL
    msg.motor_cmd = cmds
    ok = pub.Write(msg)
    print(ok)
    if not ok:
        raise RuntimeError("Publish LowCmd failed")


# ---- 6) Compose the motion: stiffen → extend fast → hold briefly → retract
serial_cmds = neutral_cmds_from(serial_states)


# Helper to apply weights/gains to selected joints by enum index
def set_pd_for(j_indices, kp, kd, weight=1.0):
    for j in j_indices:
        idx = int(j)  # enums are ints in the binding
        if 0 <= idx < len(serial_cmds):
            serial_cmds[idx].kp = kp
            serial_cmds[idx].kd = kd
            serial_cmds[idx].weight = weight


def set_targets(delta_map, scale=1.0):
    # Targets are absolute q = q0 + scale*delta
    for j, dq in delta_map.items():
        idx = int(j)
        if 0 <= idx < len(serial_cmds):
            q0 = serial_states[idx].q
            serial_cmds[idx].q = q0 + scale * dq


# Target deltas (radians) relative to current posture for a forward punch
PUNCH_DELTA = {
    J.kRightShoulderPitch: 0.0,  # shoulder pitch forward
    J.kRightElbowPitch: 0.1,  # elbow extension (negative if flexion was positive)
    # keep roll / yaw small to avoid side swing
    J.kRightShoulderRoll: -0.1,
}
# Target deltas (radians) relative to current posture for a forward punch
PUNCH_DELTA_2 = {
    J.kRightShoulderPitch: -0.0,  # shoulder pitch forward
    J.kRightElbowPitch: +0.00,  # elbow extension (negative if flexion was positive)
    J.kRightElbowYaw: -0.45,  # elbow extension (negative if flexion was positive)
    # keep roll / yaw small to avoid side swing
    J.kRightShoulderRoll: 0.00,
}

PUNCH_DELTA_BACK = {
    J.kRightShoulderPitch: +0.65,  # shoulder pitch forward
    J.kRightElbowPitch: -0.00,  # elbow extension (negative if flexion was positive)
    # keep roll / yaw small to avoid side swing
    J.kRightShoulderRoll: 0.00,
}
# Target deltas (radians) relative to current posture for a forward punch
PUNCH_DELTA_BACK_2 = {
    J.kRightShoulderPitch: -0.0,  # shoulder pitch forward
    J.kRightElbowPitch: -0.0,  # elbow extension (negative if flexion was positive)
    J.kRightElbowYaw: +0.45,  # elbow extension (negative if flexion was positive)
    # keep roll / yaw small to avoid side swing
    J.kRightShoulderRoll: 0.00,
}


# 6a) Stiffen arm at current pose
set_pd_for(ARM_JOINTS_RIGHT, kp=40.0, kd=1.0, weight=1.0)
set_targets({j: 0.0 for j in ARM_JOINTS_RIGHT}, scale=0.0)
send_serial_cmds(serial_cmds)
sleep(0.08)

# # 6b) Fast extend (the “punch”)
set_pd_for(ARM_JOINTS_RIGHT, kp=KP_MED, kd=KD_MED, weight=1.0)
set_targets(PUNCH_DELTA, scale=1.0)
send_serial_cmds(serial_cmds)
sleep(0.50)  # short dwell at extension

# 6b) Fast extend (the “punch”)
set_pd_for(ARM_JOINTS_RIGHT, kp=KP_MED, kd=KD_MED, weight=1.0)
set_targets(PUNCH_DELTA_2, scale=1.0)
send_serial_cmds(serial_cmds)
sleep(0.20)  # short dwell at extension

# 6c) Retract quickly back to start pose
set_pd_for(ARM_JOINTS_RIGHT, kp=KP_MED, kd=KD_MED, weight=1.0)
set_targets(PUNCH_DELTA_BACK, scale=1.0)
send_serial_cmds(serial_cmds)
sleep(0.50)  # short dwell at extension

# 6c) Retract quickly back to start pose
set_pd_for(ARM_JOINTS_RIGHT, kp=KP_MED, kd=KD_MED, weight=1.0)
set_targets(PUNCH_DELTA_BACK_2, scale=1.0)
send_serial_cmds(serial_cmds)
sleep(0.20)  # short dwell at extension


# 6d) Relax gains
set_pd_for(ARM_JOINTS_RIGHT, kp=40.0, kd=1.0, weight=1.0)
send_serial_cmds(serial_cmds)

# # ---- 7) Cleanup (optional; keep alive if you’ll stream more)
# pub.CloseChannel()
# sub.CloseChannel()
