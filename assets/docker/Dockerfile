# Getting ubuntu image
FROM ubuntu:18.04

# Setting arguments
ARG ZEPHYR_BRANCH
ARG ZEPHYR_URL
ARG SDK_VERSION
ARG CMAKE_VERSION
ARG USERNAME
ARG GCC_ARM_NAME

# Setting env variables
ENV user=${USERNAME}
ENV PATH="/home/${user}/.local/bin:${PATH}"
ENV ZEPHYR_BASE=/home/${user}/zephyrproject/zephyr
ENV APP=/home/${user}/workdir
ENV ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ENV ZEPHYR_SDK_INSTALL_DIR=/home/${user}/toolchains/zephyr-sdk-${SDK_VERSION} 
ENV USER_HOME=/home/${user}

# Creating directories
RUN mkdir -p ${ZEPHYR_BASE}
RUN mkdir -p /home/${user}/toolchains
RUN mkdir -p ${APP}

# Installing packages
RUN dpkg --add-architecture i386 && \
	apt-get -y update && \
	apt-get -y upgrade && \
    apt-get -y install sudo

RUN useradd -m -d /home/${user} ${user} && \
    chown -R ${user} /home/${user} && \
    adduser ${user} sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER ${user}

ENV DEBIAN_FRONTEND noninteractive

# Installing zephyr dependencias
## Installing default packages
RUN sudo apt-get install -y tzdata
RUN sudo apt-get install -y --no-install-recommends git ninja-build gperf \
  ccache dfu-util wget \
  python3-pip python3-setuptools python3-tk python3-wheel xz-utils file \
  make gcc gcc-multilib g++-multilib libsdl2-dev build-essential

## Changing workspace to tmp
RUN mkdir -p ${USER_HOME}/tmp
WORKDIR ${USER_HOME}/tmp

## Installing dtc 1.4.7
RUN wget -q https://launchpad.net/ubuntu/+source/device-tree-compiler/1.4.7-1/+build/15279267/+files/device-tree-compiler_1.4.7-1_amd64.deb && \
        sudo dpkg -i device-tree-compiler_1.4.7-1_amd64.deb 

## Installing Cmake
RUN wget -q https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-Linux-x86_64.sh && \
	chmod +x cmake-${CMAKE_VERSION}-Linux-x86_64.sh && \
	sudo ./cmake-${CMAKE_VERSION}-Linux-x86_64.sh --skip-license --prefix=/usr/local && \
	rm -f ./cmake-${CMAKE_VERSION}-Linux-x86_64.sh

## Installing zephyr sdk
RUN wget -q "https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${SDK_VERSION}/zephyr-sdk-${SDK_VERSION}-setup.run"
RUN sh "zephyr-sdk-${SDK_VERSION}-setup.run" --quiet -- -d ${ZEPHYR_SDK_INSTALL_DIR} -y
RUN rm "zephyr-sdk-${SDK_VERSION}-setup.run"

## Installing GCC_ARM
RUN wget -q https://developer.arm.com/-/media/Files/downloads/gnu-rm/9-2019q4/RC2.1/${GCC_ARM_NAME}-x86_64-linux.tar.bz2  && \
	tar xf ${GCC_ARM_NAME}-x86_64-linux.tar.bz2 && \
	rm -f ${GCC_ARM_NAME}-x86_64-linux.tar.bz2 && \
	mv ${GCC_ARM_NAME} /home/${user}/toolchains/${GCC_ARM_NAME}

# Getting zephyr and creating the environment 
#TODO: Ponto de falha por sempre utilizar o requirements do master. Isso foi feito pois em versões antigas do zephyr os requirements estavam quebrados.
RUN git clone -q -b ${ZEPHYR_BRANCH} --single-branch ${ZEPHYR_URL} ${ZEPHYR_BASE}
RUN pip3 install wheel && \
        #wget -q https://raw.githubusercontent.com/zephyrproject-rtos/zephyr/master/scripts/requirements.txt && \
	pip3 install -r ${ZEPHYR_BASE}/scripts/requirements.txt && \
    #rm -f requirements.txt && \
	pip3 install sh
RUN pip3 install --user -U west

## Initializing west environment
RUN (cd ${ZEPHYR_BASE}/.. && west init -l ${ZEPHYR_BASE} && west update)

# Download nRF Command Line Tools
RUN wget -qO nrf5_tools.tar.gz https://www.nordicsemi.com/-/media/Software-and-other-downloads/Desktop-software/nRF-command-line-tools/sw/Versions-10-x-x/nRFCommandLineTools1021Linuxamd64tar.gz

# Extract nRF Command Line Tools
RUN mkdir nrf5_tools
RUN tar -xvzf nrf5_tools.tar.gz -C nrf5_tools

# Install JLink and nRF Command Line Tools
RUN sudo dpkg -i nrf5_tools/JLink_Linux_V644e_x86_64.deb
RUN sudo dpkg -i nrf5_tools/nRF-Command-Line-Tools_10_2_1_Linux-amd64.deb

RUN rm -rf nrf5_tools nrf5_tools.tar.gz

# Install mcuboot
ENV MCUBOOT_FOLDER=${ZEPHYR_BASE}/../mcuboot
WORKDIR ${ZEPHYR_BASE}/.. 
RUN git clone -q https://github.com/JuulLabs-OSS/mcuboot

## Installing dependencies to use mcuboot succesfully
RUN pip3 install cryptography

# Setting locales and language
RUN sudo apt-get install -y locales
RUN sudo locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Install vim
RUN sudo apt-get -y install vim

# Install st-flash
WORKDIR ${USER_HOME}/tmp
RUN sudo apt-get -y install libusb-1.0
RUN git clone -q https://github.com/texane/stlink.git
WORKDIR ${USER_HOME}/tmp/stlink
RUN make
RUN cd build/Release && sudo make install 
ENV LD_LIBRARY_PATH=/usr/local/lib

# Giving additional permissions to user
RUN sudo usermod -a -G dialout ${user}

CMD ["/bin/bash"]

WORKDIR ${APP}
VOLUME ${APP}
ENV PORTS_DEV=/dev
VOLUME ${PORTS_DEV}

