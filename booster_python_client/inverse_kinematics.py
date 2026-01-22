import numpy as np


def _clamp(x, lo=-1.0, hi=1.0):
    return np.minimum(hi, np.maximum(lo, x))


def _unit(v, eps=1e-9):
    n = np.linalg.norm(v)
    if n < eps:
        raise ValueError("Zero/near-zero vector; target too close to shoulder.")
    return v / n


def _rodrigues(v, axis, ang):
    # Rotate vector v about unit axis by ang
    k = _unit(axis)
    c = np.cos(ang)
    s = np.sin(ang)
    return v * c + np.cross(k, v) * s + k * (np.dot(k, v)) * (1 - c)


def _Rx(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], float)


def _Ry(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], float)


def ik_left_arm_numpy(
    p_shoulder,  # np.array([x,y,z]) target hand position in SHOULDER frame
    L1,
    L2,  # upper arm length, forearm length
    elbow_sign=+1,  # +1 / -1 chooses the two elbow configurations
    elbow_out_ref=np.array(
        [0.0, 1.0, 0.0]
    ),  # preferred elbow "out" direction (left = +y)
    elbow_yaw=0.0,  # free DOF unless you have a twist target
    solve_elbow_yaw=True,
):
    """
    Assumed convention (common & practical):
      - Shoulder frame axes: x forward, y left, z up.
      - When shoulderPitch=shoulderRoll=0, upper arm points down along -z.
      - Shoulder direction model: u_hat = Rx(roll) @ Ry(pitch) @ [0,0,-1]
      - ElbowPitch = 0 means arm is straight; positive bends the elbow.
    Returns: (shoulder_pitch, shoulder_roll, elbow_pitch, elbow_yaw)
    """
    p = np.asarray(p_shoulder, dtype=float)
    d = np.linalg.norm(p)
    if d < 1e-9:
        raise ValueError("Target too close to shoulder origin.")

    # Reachability
    if d > (L1 + L2) + 1e-6 or d < abs(L1 - L2) - 1e-6:
        raise ValueError("Target out of reach.")

    # ElbowPitch (0 = straight)
    c_el = (L1**2 + L2**2 - d**2) / (2.0 * L1 * L2)
    c_el = float(_clamp(c_el))
    elbow_pitch = np.pi - np.arccos(c_el)

    # Angle between target direction and upper-arm direction
    c_beta = (L1**2 + d**2 - L2**2) / (2.0 * L1 * d)
    c_beta = float(_clamp(c_beta))
    beta = np.arccos(c_beta)

    t_hat = _unit(p)

    # Choose a bend plane using a reference direction
    ref = np.asarray(elbow_out_ref, dtype=float)
    axis = np.cross(t_hat, ref)
    if np.linalg.norm(axis) < 1e-6:
        ref = np.array([1.0, 0.0, 0.0])
        axis = np.cross(t_hat, ref)
        if np.linalg.norm(axis) < 1e-6:
            raise ValueError("Degenerate bend axis; choose a different elbow_out_ref.")

    # Upper arm direction (elbow-up/down) by rotating t_hat by ±beta about axis
    u_hat = _rodrigues(t_hat, axis, elbow_sign * beta)
    ux, uy, uz = u_hat

    # Solve shoulder pitch/roll from u_hat = Rx(roll) Ry(pitch) [0,0,-1]
    shoulder_pitch = np.arctan2(ux, np.sqrt(uy**2 + uz**2))
    shoulder_roll = np.arctan2(uy, -uz)

    if solve_elbow_yaw:
        R_sh = _Rx(shoulder_roll) @ _Ry(shoulder_pitch)
        elbow = u_hat * L1
        f = p - elbow
        f_hat = _unit(f)
        f_hat_sh = R_sh.T @ f_hat
        elbow_yaw = np.arctan2(f_hat_sh[1], f_hat_sh[0])
        elbow_pitch = np.arctan2(np.linalg.norm(f_hat_sh[:2]), -f_hat_sh[2])

    return (
        float(shoulder_pitch),
        float(shoulder_roll),
        float(elbow_pitch),
        float(elbow_yaw),
    )
