#include <memory>
#include <string>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "trajectory_msgs/msg/joint_trajectory.hpp"
#include "trajectory_msgs/msg/joint_trajectory_point.hpp"
class MoveItMotionController : public rclcpp::Node {
public:
  MoveItMotionController() : Node("moveit_motion_controller") {
    sub_ = create_subscription<std_msgs::msg::String>("/motion/plan_request", 10, [this](const std_msgs::msg::String::SharedPtr msg){ plan(msg->data); });
    pub_ = create_publisher<trajectory_msgs::msg::JointTrajectory>("/motion/joint_trajectory", 10);
  }
private:
  void plan(const std::string & request) {
    trajectory_msgs::msg::JointTrajectory traj;
    traj.joint_names = {"joint1","joint2","joint3","joint4","joint5","joint6"};
    trajectory_msgs::msg::JointTrajectoryPoint point;
    point.positions = {0.0, 0.1, 0.2, 0.1, 0.0, 0.0};
    point.time_from_start = rclcpp::Duration::from_seconds(1.0);
    traj.points.push_back(point);
    RCLCPP_INFO(get_logger(), "planned MoveIt trajectory for %s", request.c_str());
    pub_->publish(traj);
  }
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub_; rclcpp::Publisher<trajectory_msgs::msg::JointTrajectory>::SharedPtr pub_;
};
int main(int argc, char ** argv){ rclcpp::init(argc, argv); rclcpp::spin(std::make_shared<MoveItMotionController>()); rclcpp::shutdown(); return 0; }
