import json
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64
import zenoh

class BridgeNode(Node):
    def __init__(self):
        super().__init__('bridge_node')

        self.declare_parameter('zenoh_listen_endpoint', 'tcp/0.0.0.0:7447')
        self.declare_parameter('zenoh_state_key', 'mujoco/sim/joint_states')
        self.declare_parameter('zenoh_cmd_key', 'mujoco/sim/cmd_torque')
        self.declare_parameter('joint_name', 'hinge')
        self.declare_parameter('frame_id', 'world')

        listen_endpoint = self.get_parameter('zenoh_listen_endpoint').value
        state_key = self.get_parameter('zenoh_state_key').value
        cmd_key = self.get_parameter('zenoh_cmd_key').value
        self.joint_name = self.get_parameter('joint_name').value
        self.frame_id = self.get_parameter('frame_id').value

        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.torque_sub = self.create_subscription(Float64, '/cmd_torque', self.torque_callback, 10)

        # configure Zenoh to host the TCP server directly
        self.zenoh_conf = zenoh.Config()
        self.zenoh_conf.insert_json5("mode", json.dumps("peer"))
        self.zenoh_conf.insert_json5("listen/endpoints", json.dumps([listen_endpoint]))
        
        self.get_logger().info(f"Hosting Zenoh server on {listen_endpoint}...")
        self.zenoh_session = zenoh.open(self.zenoh_conf)
        
        self.zenoh_sub = self.zenoh_session.declare_subscriber(state_key, self.zenoh_state_listener)
        self.zenoh_pub = self.zenoh_session.declare_publisher(cmd_key)

        self.get_logger().info("BridgeNode is live and ready for native macOS connections.")

    def zenoh_state_listener(self, sample):
        try:
            payload_str = sample.payload.to_bytes().decode('utf-8')
            data = json.loads(payload_str)

            msg = JointState()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = self.frame_id
            msg.name = [self.joint_name]
            msg.position = [float(data['position'])]
            msg.velocity = [float(data['velocity'])]

            self.joint_pub.publish(msg)
        except Exception as e:
            self.get_logger().warn(f"Telemetry parse error: {e}", throttle_duration_sec=2.0)

    def torque_callback(self, msg: Float64):
        payload = json.dumps({'torque': float(msg.data)})
        self.zenoh_pub.put(payload.encode('utf-8'))

    def destroy_node(self):
        if hasattr(self, 'zenoh_session'):
            self.zenoh_session.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = BridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()