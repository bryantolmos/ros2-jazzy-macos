import time
import json
import mujoco
import mujoco.viewer
import zenoh

COLIMA_IP = "192.168.64.2"

MJCF_MODEL = """
<mujoco model="inverted_pendulum">
  <option gravity="0 0 -9.81" timestep="0.002"/>
  <worldbody>
    <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
    <geom type="plane" size="1 1 0.1"/>
    <body name="pole" pos="0 0 1.2">
      <joint name="hinge" type="hinge" axis="0 1 0" damping="0.005"/>
      <geom type="cylinder" size="0.03 0.4" pos="0 0 0.4" rgba="0.8 0.2 0.2 1"/>
    </body>
  </worldbody>
  <actuator>
    <motor name="hinge_motor" joint="hinge" gear="1" ctrllimited="true" ctrlrange="-10.0 10.0"/>
  </actuator>
</mujoco>
"""

applied_torque = 0.0

def torque_listener(sample):
    global applied_torque
    payload_str = sample.payload.to_bytes().decode('utf-8')
    data = json.loads(payload_str)
    applied_torque = float(data.get('torque', 0.0))

def main():
    print(f"Connecting to Zenoh router at tcp/{COLIMA_IP}:7447...")
    conf = zenoh.Config()
    conf.insert_json5("mode", json.dumps("client"))
    conf.insert_json5("connect/endpoints", json.dumps([f"tcp/{COLIMA_IP}:7447"]))
    session = zenoh.open(conf)
    
    # matching namespaced keys
    pub_states = session.declare_publisher("mujoco/sim/joint_states")
    sub_torque = session.declare_subscriber("mujoco/sim/cmd_torque", torque_listener)
    print("Zenoh connection active. Streaming states and listening for actuation...")

    model = mujoco.MjModel.from_xml_string(MJCF_MODEL)
    data = mujoco.MjData(model)

    data.qpos[0] = 0.15
    mujoco.mj_forward(model, data)

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            step_start = time.time()
            
            data.ctrl[0] = applied_torque
            mujoco.mj_step(model, data)
            
            payload = json.dumps({
                "position": float(data.qpos[0]),
                "velocity": float(data.qvel[0])
            })
            pub_states.put(payload.encode("utf-8"))
            
            viewer.sync()
            
            dt = model.opt.timestep - (time.time() - step_start)
            if dt > 0:
                time.sleep(dt)

    session.close()

if __name__ == "__main__":
    main()