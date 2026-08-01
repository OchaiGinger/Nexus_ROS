from setuptools import setup
package_name='lcd_status_node'
setup(name=package_name, version='0.2.0', packages=[package_name], data_files=[('share/ament_index/resource_index/packages',['resource/'+package_name]),('share/'+package_name,['package.xml']),('share/'+package_name+'/config',['config/lcd_status_node.yaml'])], install_requires=['setuptools'], zip_safe=True, maintainer='Nexus Robotics', maintainer_email='nexus@example.com', description='Nexus lcd_status_node.', license='MIT', entry_points={'console_scripts':['lcd_status_node = lcd_status_node.node:main']})
