from setuptools import setup
package_name='tof_calibration'
setup(name=package_name, version='0.2.0', packages=[package_name], data_files=[('share/ament_index/resource_index/packages',['resource/'+package_name]),('share/'+package_name,['package.xml']),('share/'+package_name+'/config',['config/tof_calibration.yaml'])], install_requires=['setuptools'], zip_safe=True, maintainer='Nexus Robotics', maintainer_email='nexus@example.com', description='Nexus tof_calibration.', license='MIT', entry_points={'console_scripts':['tof_calibration = tof_calibration.node:main']})
