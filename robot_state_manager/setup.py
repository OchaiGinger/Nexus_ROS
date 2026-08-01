from setuptools import setup
package_name='robot_state_manager'
setup(name=package_name, version='0.2.0', packages=[package_name], data_files=[('share/ament_index/resource_index/packages',['resource/'+package_name]),('share/'+package_name,['package.xml']),('share/'+package_name+'/config',['config/robot_state_manager.yaml'])], install_requires=['setuptools'], zip_safe=True, maintainer='Nexus Robotics', maintainer_email='nexus@example.com', description='Nexus robot_state_manager.', license='MIT', entry_points={'console_scripts':['robot_state_manager = robot_state_manager.node:main']})
