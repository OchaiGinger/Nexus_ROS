from setuptools import setup
package_name='camera_driver'
setup(name=package_name, version='0.2.0', packages=[package_name], data_files=[('share/ament_index/resource_index/packages',['resource/'+package_name]),('share/'+package_name,['package.xml']),('share/'+package_name+'/config',['config/camera_driver.yaml'])], install_requires=['setuptools'], zip_safe=True, maintainer='Nexus Robotics', maintainer_email='nexus@example.com', description='Nexus camera_driver.', license='MIT', entry_points={'console_scripts':['camera_driver = camera_driver.node:main']})
