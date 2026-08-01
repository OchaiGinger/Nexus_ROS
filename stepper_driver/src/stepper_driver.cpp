#include <memory>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "trajectory_msgs/msg/joint_trajectory.hpp"
class StepperDriver : public rclcpp::Node {
public:
  StepperDriver() : Node("stepper_driver") {
    sub_ = create_subscription<trajectory_msgs::msg::JointTrajectory>("/motion/joint_trajectory", 10, [this](const trajectory_msgs::msg::JointTrajectory::SharedPtr msg){ execute(*msg); });
    status_ = create_publisher<std_msgs::msg::String>("/motion/stepper_status", 10);
  }
private:
  void execute(const trajectory_msgs::msg::JointTrajectory & traj) {
    std_msgs::msg::String status; status.data = traj.joint_names.size() == 6 ? "DONE" : "ERROR_EXPECTED_6_AXES"; RCLCPP_INFO(get_logger(), "stepper execution %s", status.data.c_str()); status_->publish(status);
  }
  rclcpp::Subscription<trajectory_msgs::msg::JointTrajectory>::SharedPtr sub_; rclcpp::Publisher<std_msgs::msg::String>::SharedPtr status_;
};
int main(int argc, char ** argv){ rclcpp::init(argc, argv); rclcpp::spin(std::make_shared<StepperDriver>()); rclcpp::shutdown(); return 0; }
