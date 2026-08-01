from setuptools import setup

package_name = 'nexus_robot_system'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=False,
    author='Nexus Robotics',
    author_email='nexus@example.com',
    description='Middleware, perception, sensor, audio, LCD, and MoveIt orchestration for Nexus robot frontend instructions.',
    entry_points={
        'console_scripts': [
            'middleware_bridge = nexus_robot_system.middleware_bridge:main',
            'moveit_action_executor = nexus_robot_system.moveit_action_executor:main',
            'yolo_grid_perception = nexus_robot_system.yolo_grid_perception:main',
            'tof_calibration_node = nexus_robot_system.tof_calibration_node:main',
            'lcd_status_node = nexus_robot_system.lcd_status_node:main',
            'speaker_node = nexus_robot_system.speaker_node:main',
        ],
    },
)
