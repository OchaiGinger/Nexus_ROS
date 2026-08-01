from setuptools import setup
package_name='speaker_node'
setup(name=package_name, version='0.2.0', packages=[package_name], data_files=[('share/ament_index/resource_index/packages',['resource/'+package_name]),('share/'+package_name,['package.xml']),('share/'+package_name+'/config',['config/speaker_node.yaml'])], install_requires=['setuptools'], zip_safe=True, maintainer='Nexus Robotics', maintainer_email='nexus@example.com', description='Nexus speaker_node.', license='MIT', entry_points={'console_scripts':['speaker_node = speaker_node.node:main']})
