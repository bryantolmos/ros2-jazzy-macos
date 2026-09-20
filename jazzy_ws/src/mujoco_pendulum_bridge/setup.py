import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'mujoco_pendulum_bridge'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Bryant Olmos',
    maintainer_email='olmosbryan29@gmail.com',
    description='FOSS ROS 2 Jazzy bridge and closed-loop controller for native macOS MuJoCo simulations.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'bridge_node = mujoco_pendulum_bridge.bridge_node:main',
            'controller_node = mujoco_pendulum_bridge.controller_node:main',
        ],
    },
)