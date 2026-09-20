FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV PYTHONPATH="/opt/ros/jazzy/lib/python3.12/site-packages:$PYTHONPATH"
ENV PATH="/opt/ros/jazzy/bin:$PATH"
ENV LD_LIBRARY_PATH="/opt/ros/jazzy/lib:$LD_LIBRARY_PATH"
ENV AMENT_PREFIX_PATH="/opt/ros/jazzy"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && echo "deb [trusted=yes] https://download.eclipse.org/zenoh/debian-repo/ /" | tee /etc/apt/sources.list.d/zenoh.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    python3-colcon-common-extensions \
    python3-pip \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-sensor-msgs \
    zenoh-bridge-ros2dds \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir eclipse-zenoh

WORKDIR /jazzy_ws
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc

CMD ["bash"]