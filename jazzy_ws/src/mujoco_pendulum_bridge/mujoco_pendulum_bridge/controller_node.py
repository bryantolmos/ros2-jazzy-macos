import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64

class ControllerNode(Node):
    def __init__(self):
        super().__init__('controller_node')

        self.declare_parameter('target_angle', 0.0)
        self.declare_parameter('kp', 45.0)
        self.declare_parameter('kd', 6.5)
        self.declare_parameter('max_torque', 10.0)

        self.declare_parameter('push_duration', 0.35)
        self.declare_parameter('push_torque', 8.0)
        self.declare_parameter('free_duration', 5.0)
        self.declare_parameter('stabilize_duration', 5.0)

        self.sub_state = self.create_subscription(
            JointState,
            '/joint_states',
            self.state_callback,
            10
        )
        self.pub_torque = self.create_publisher(Float64, '/cmd_torque', 10)

        self.cycle_start_time = self.get_clock().now().nanoseconds / 1e9
        self.current_state = 'PUSH'
        self.get_logger().info("ControllerNode initialized. Starting cyclic demo sequence.")

    def state_callback(self, msg: JointState):
        if not msg.position or not msg.velocity:
            return

        pos = msg.position[0]
        vel = msg.velocity[0]

        now = self.get_clock().now().nanoseconds / 1e9
        elapsed = now - self.cycle_start_time

        push_dur = self.get_parameter('push_duration').value
        push_trq = self.get_parameter('push_torque').value
        free_dur = self.get_parameter('free_duration').value
        stab_dur = self.get_parameter('stabilize_duration').value
        total_cycle = push_dur + free_dur + stab_dur

        # reset cycle timer
        if elapsed >= total_cycle:
            self.cycle_start_time = now
            elapsed = 0.0

        # strong push
        if elapsed < push_dur:
            if self.current_state != 'PUSH':
                self.current_state = 'PUSH'
                self.get_logger().info(f">>> Mode: PUSH - Applying disturbance torque kick ({push_trq:+.1f} N*m)")
            
            torque = push_trq

        # free swing
        elif elapsed < (push_dur + free_dur):
            if self.current_state != 'FREE':
                self.current_state = 'FREE'
                self.get_logger().info(f">>> Mode: FREE SWING - Coasting unactuated for {free_dur:.1f}s")
            
            torque = 0.0

        # stabilization
        else:
            if self.current_state != 'STABILIZE':
                self.current_state = 'STABILIZE'
                self.get_logger().info(">>> Mode: STABILIZE - Engaging PD control to catch & balance upright")

            target_angle = self.get_parameter('target_angle').value
            kp = self.get_parameter('kp').value
            kd = self.get_parameter('kd').value
            max_torque = self.get_parameter('max_torque').value

            # wrap angular error to [-pi, pi]
            error = (target_angle - pos + math.pi) % (2.0 * math.pi) - math.pi
            
            # PD control law: tau = Kp * error - Kd * velocity
            torque = (kp * error) - (kd * vel)
            torque = max(min(torque, max_torque), -max_torque)

        cmd = Float64()
        cmd.data = float(torque)
        self.pub_torque.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = ControllerNode()
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