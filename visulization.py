import os
import numpy as np
import xml.etree.ElementTree as ET


def rpy_to_R(rpy):
    r, p, y = rpy
    cr, sr = np.cos(r), np.sin(r)
    cp, sp = np.cos(p), np.sin(p)
    cy, sy = np.cos(y), np.sin(y)
    # Rz(yaw) @ Ry(pitch) @ Rx(roll)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return Rz @ Ry @ Rx


def T_of(xyz, rpy=None):
    M = np.eye(4)
    M[:3, 3] = xyz
    if rpy is not None:
        M[:3, :3] = rpy_to_R(rpy)
    return M


def R_axis_angle(axis, a):
    axis = np.asarray(axis, float)
    axis = axis / (np.linalg.norm(axis) + 1e-12)
    x, y, z = axis
    c, s = np.cos(a), np.sin(a)
    C = 1 - c
    R = np.array(
        [
            [c + x * x * C, x * y * C - z * s, x * z * C + y * s],
            [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
            [z * x * C - y * s, z * y * C + x * s, c + z * z * C],
        ],
        dtype=float,
    )
    M = np.eye(4)
    M[:3, :3] = R
    return M


def load_urdf_left_arm(urdf_path):
    import xml.etree.ElementTree as ET

    tree = ET.parse(urdf_path)
    root = tree.getroot()
    base_dir = os.path.dirname(os.path.abspath(urdf_path))

    def get_joint(jname):
        j = root.find(f"./joint[@name='{jname}']")
        if j is None:
            raise ValueError(f"Joint not found: {jname}")
        parent = j.find("parent").attrib["link"]
        child = j.find("child").attrib["link"]

        origin = j.find("origin")
        xyz = (
            np.fromstring(origin.attrib.get("xyz", "0 0 0"), sep=" ")
            if origin is not None
            else np.zeros(3)
        )
        rpy = (
            np.fromstring(origin.attrib.get("rpy", "0 0 0"), sep=" ")
            if origin is not None
            else np.zeros(3)
        )

        axis = j.find("axis")
        ax = (
            np.fromstring(axis.attrib.get("xyz", "0 0 1"), sep=" ")
            if axis is not None
            else np.array([0, 0, 1.0])
        )
        return dict(name=jname, parent=parent, child=child, xyz=xyz, rpy=rpy, axis=ax)

    def get_link_mesh(link_name):
        link = root.find(f"./link[@name='{link_name}']")
        if link is None:
            return None

        vis = link.find("visual")
        if vis is None:
            return None

        origin = vis.find("origin")
        v_xyz = (
            np.fromstring(origin.attrib.get("xyz", "0 0 0"), sep=" ")
            if origin is not None
            else np.zeros(3)
        )
        v_rpy = (
            np.fromstring(origin.attrib.get("rpy", "0 0 0"), sep=" ")
            if origin is not None
            else np.zeros(3)
        )

        geom = vis.find("geometry")
        mesh = geom.find("mesh") if geom is not None else None
        if mesh is None:
            return None

        fname = mesh.attrib["filename"]  # e.g. meshes/AL1.STL
        scale = np.fromstring(mesh.attrib.get("scale", "1 1 1"), sep=" ")
        abs_path = os.path.join(base_dir, fname)
        return dict(
            link=link_name, path=abs_path, scale=scale, vis_xyz=v_xyz, vis_rpy=v_rpy
        )

    joints = [
        get_joint("Left_Shoulder_Pitch"),
        get_joint("Left_Shoulder_Roll"),
        get_joint("Left_Elbow_Pitch"),
        get_joint("Left_Elbow_Yaw"),
    ]

    # meshes we’ll render (trunk + the left arm chain)
    mesh_links = ["Trunk", "AL1", "AL2", "AL3", "left_hand_link"]
    meshes = {ln: get_link_mesh(ln) for ln in mesh_links}

    return joints, meshes


def fk_left_arm(joints, q):
    """
    q: dict with keys matching joint names above, radians.
    Returns a dict of link->T_world_link (world == Trunk frame here).
    """
    T_link = {"Trunk": np.eye(4)}

    # Walk the chain; each joint defines: parent_link -> child_link
    for j in joints:
        parent = j["parent"]
        child = j["child"]
        qj = float(q.get(j["name"], 0.0))

        # URDF convention: T_parent_child = T(origin xyz,rpy) * R(axis, q)
        T_origin = T_of(j["xyz"], j["rpy"])
        T_rot = R_axis_angle(j["axis"], qj)

        T_link[child] = T_link[parent] @ T_origin @ T_rot

    return T_link


def _rpy_to_R(rpy):
    r, p, y = rpy
    cr, sr = np.cos(r), np.sin(r)
    cp, sp = np.cos(p), np.sin(p)
    cy, sy = np.cos(y), np.sin(y)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return Rz @ Ry @ Rx


def _T(xyz, rpy):
    M = np.eye(4)
    M[:3, 3] = xyz
    M[:3, :3] = _rpy_to_R(rpy)
    return M


def arm_lengths_from_urdf(urdf_path):
    root = ET.parse(urdf_path).getroot()

    def joint_origin(jname):
        j = root.find(f"./joint[@name='{jname}']")
        if j is None:
            raise ValueError(f"Joint not found: {jname}")
        parent = j.find("parent").attrib["link"]
        child = j.find("child").attrib["link"]
        origin = j.find("origin")
        xyz = (
            np.fromstring(origin.attrib.get("xyz", "0 0 0"), sep=" ")
            if origin is not None
            else np.zeros(3)
        )
        rpy = (
            np.fromstring(origin.attrib.get("rpy", "0 0 0"), sep=" ")
            if origin is not None
            else np.zeros(3)
        )
        return parent, child, _T(xyz, rpy)

    # chain (zero angles): Trunk -> AL1 -> AL2 -> AL3 -> left_hand_link
    _, AL1, T1 = joint_origin("Left_Shoulder_Pitch")
    _, AL2, T2 = joint_origin("Left_Shoulder_Roll")
    _, AL3, T3 = joint_origin("Left_Elbow_Pitch")
    _, HAND, T4 = joint_origin("Left_Elbow_Yaw")

    T_trunk = np.eye(4)
    T_AL1 = T_trunk @ T1
    T_AL2 = T_AL1 @ T2
    T_AL3 = T_AL2 @ T3
    T_hand = T_AL3 @ T4

    # joint origins in Trunk frame (at zero angles)
    p_shoulder_roll = T_AL2[:3, 3]
    p_elbow_pitch = T_AL3[:3, 3]
    p_elbow_yaw = T_hand[:3, 3]  # also left_hand_link origin here

    L1 = np.linalg.norm(p_elbow_pitch - p_shoulder_roll)
    L2 = np.linalg.norm(p_elbow_yaw - p_elbow_pitch)
    return L1, L2, L1 + L2


import numpy as np
import matplotlib.pyplot as plt
from booster_python_client.inverse_kinematics import ik_left_arm_numpy


# ---------------- Simple FK for visualization ----------------
def Rx(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)


def Ry(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], float)


def Rz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)


def fk_points(q_sp, q_sr, q_ep, q_ey, L1, L2):
    """
    Matches the IK convention:
      u_hat = Rx(roll) @ Ry(pitch) @ [0,0,-1]
    """
    R_sh = Rx(q_sr) @ Ry(q_sp)

    shoulder = np.array([0.0, 0.0, 0.0])
    elbow = shoulder + R_sh @ np.array([0.0, 0.0, -L1])

    R_el = R_sh @ Rz(q_ey) @ Ry(q_ep)
    hand = elbow + R_el @ np.array([0.0, 0.0, -L2])

    return shoulder, elbow, hand


# ---------------- Robust interactive viz ----------------
class ArmViz:
    def __init__(self, L1=0.20, L2=0.20):
        self.L1, self.L2 = float(L1), float(L2)
        self.p = np.array([0.15, 0.15, -0.15], float)
        self.step = 0.01
        self.elbow_sign = +1

        self.keys_down = set()
        self.last_key = None

        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection="3d")

        self.cid_press = self.fig.canvas.mpl_connect("key_press_event", self.on_press)
        self.cid_release = self.fig.canvas.mpl_connect(
            "key_release_event", self.on_release
        )

        (self.arm_line,) = self.ax.plot([], [], [], linewidth=3)
        (self.target_pt,) = self.ax.plot(
            [], [], [], marker="o", markersize=8, linestyle="None"
        )
        (self.reached_pt,) = self.ax.plot(
            [], [], [], marker="o", markersize=6, linestyle="None"
        )
        self.status = self.ax.text2D(
            0.02, 0.98, "", transform=self.ax.transAxes, va="top"
        )

        self._setup_axes()

        # Timer loop to update continuously (handles "held keys")
        self.timer = self.fig.canvas.new_timer(interval=30)  # ms
        self.timer.add_callback(self.tick)
        self.timer.start()

        # Important: focus the window
        self.fig.canvas.manager.set_window_title(
            "ArmViz (click here, then use arrow keys)"
        )

        self.update()

    def _setup_axes(self):
        L = self.L1 + self.L2
        lim = L * 1.2
        self.ax.set_xlim(-lim, lim)
        self.ax.set_ylim(-lim, lim)
        self.ax.set_zlim(-lim, lim)
        self.ax.set_xlabel("X (forward)")
        self.ax.set_ylabel("Y (left)")
        self.ax.set_zlabel("Z (up)")
        self.ax.set_title("Click the figure, then use arrow keys. PgUp/PgDn = Z")

    def on_press(self, e):
        if e.key is None:
            return
        self.last_key = e.key
        self.keys_down.add(e.key)

        # one-shot keys
        if e.key in ("escape",):
            plt.close(self.fig)
        elif e.key in ("e", "E"):
            self.elbow_sign *= -1
        elif e.key in ("r", "R"):
            self.p[:] = [0.15, 0.15, -0.15]
            self.elbow_sign = +1

    def on_release(self, e):
        if e.key is None:
            return
        self.keys_down.discard(e.key)

    def tick(self):
        # Apply held-key movement
        moved = False
        if "left" in self.keys_down:
            self.p[1] -= self.step
            moved = True
        if "right" in self.keys_down:
            self.p[1] += self.step
            moved = True
        if "up" in self.keys_down:
            self.p[0] += self.step
            moved = True
        if "down" in self.keys_down:
            self.p[0] -= self.step
            moved = True
        if "pageup" in self.keys_down:
            self.p[2] += self.step
            moved = True
        if "pagedown" in self.keys_down:
            self.p[2] -= self.step
            moved = True

        if moved:
            self.update()

    def update(self):
        self.target_pt.set_data([self.p[0]], [self.p[1]])
        self.target_pt.set_3d_properties([self.p[2]])

        ok = True
        msg = ""
        try:
            q_sp, q_sr, q_ep, q_ey = ik_left_arm_numpy(
                self.p, self.L1, self.L2, elbow_sign=self.elbow_sign
            )
            shoulder, elbow, hand = fk_points(q_sp, q_sr, q_ep, q_ey, self.L1, self.L2)
            err = np.linalg.norm(hand - self.p)
        except Exception as ex:
            ok = False
            shoulder = elbow = hand = np.zeros(3)
            err = np.nan
            msg = str(ex)

        xs = [shoulder[0], elbow[0], hand[0]]
        ys = [shoulder[1], elbow[1], hand[1]]
        zs = [shoulder[2], elbow[2], hand[2]]
        self.arm_line.set_data(xs, ys)
        self.arm_line.set_3d_properties(zs)

        self.reached_pt.set_data([hand[0]], [hand[1]])
        self.reached_pt.set_3d_properties([hand[2]])

        if ok:
            self.status.set_text(
                f"target = {self.p.round(3)} m\n"
                f"elbow_sign = {self.elbow_sign:+d}\n"
                f"error = {err:.4f} m\n"
                f"last_key = {self.last_key}\n"
                f"keys_down = {sorted(self.keys_down)}\n"
                f"controls: arrows=XY, PgUp/PgDn=Z, E=toggle elbow, R=reset, Esc=quit\n"
                f"(Click inside the plot window first!)"
            )
        else:
            self.status.set_text(
                f"target = {self.p.round(3)} m\n"
                f"IK failed: {msg}\n"
                f"last_key = {self.last_key}\n"
                f"keys_down = {sorted(self.keys_down)}\n"
                f"(Move target closer / toggle elbow with E)"
            )

        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    L1, L2, _ = arm_lengths_from_urdf("models/T1_serial.urdf")
    ArmViz(L1=L1, L2=L2)
    plt.show()
