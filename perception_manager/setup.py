from setuptools import setup
package_name='perception_manager'
setup(name=package_name, version='0.2.0', packages=[package_name], data_files=[('share/ament_index/resource_index/packages',['resource/'+package_name]),('share/'+package_name,['package.xml']),('share/'+package_name+'/config',['config/perception_manager.yaml'])], install_requires=['setuptools'], zip_safe=True, maintainer='Nexus Robotics', maintainer_email='nexus@example.com', description='Nexus perception_manager.', license='MIT', entry_points={'console_scripts':['perception_manager = perception_manager.node:main']})
