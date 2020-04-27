# Getting ubuntu image
FROM ubuntu:18.04

# Setting env variables
ENV DEBIAN_FRONTEND noninteractive
ENV user=user
ENV PATH="/home/${user}/.local/bin:${PATH}"
ENV ZEPHYR_BASE=/home/${user}/zephyrproject/zephyr
ENV APP=/home/${user}/workdir
ENV ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ENV ZEPHYR_SDK_INSTALL_DIR=/home/${user}/toolchains/zephyr-sdk-0.11.1 
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
RUN wget -q https://github.com/Kitware/CMake/releases/download/v3.16.2/cmake-3.16.2-Linux-x86_64.sh && \
	chmod +x cmake-3.16.2-Linux-x86_64.sh && \
	sudo ./cmake-3.16.2-Linux-x86_64.sh --skip-license --prefix=/usr/local && \
	rm -f ./cmake-3.16.2-Linux-x86_64.sh

## Installing zephyr sdk
RUN wget -q "https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.11.1/zephyr-sdk-0.11.1-setup.run"
RUN sh "zephyr-sdk-0.11.1-setup.run" --quiet -- -d ${ZEPHYR_SDK_INSTALL_DIR} -y
RUN rm "zephyr-sdk-0.11.1-setup.run"

## Installing GCC_ARM
RUN wget -q https://developer.arm.com/-/media/Files/downloads/gnu-rm/9-2019q4/RC2.1/gcc-arm-none-eabi-9-2019-q4-major-x86_64-linux.tar.bz2  && \
	tar xf gcc-arm-none-eabi-9-2019-q4-major-x86_64-linux.tar.bz2 && \
	rm -f gcc-arm-none-eabi-9-2019-q4-major-x86_64-linux.tar.bz2 && \
	mv gcc-arm-none-eabi-9-2019-q4-major /home/${user}/toolchains/gcc-arm-none-eabi-9-2019-q4-major

# Getting zephyr and creating the environment 
#TODO: Ponto de falha por sempre utilizar o requirements do master. Isso foi feito pois em versões antigas do zephyr os requirements estavam quebrados.
RUN git clone -q -b v2.2-branch --single-branch https://github.com/zephyrproject-rtos/zephyr ${ZEPHYR_BASE}
RUN pip3 install wheel && \
        #wget -q https://raw.githubusercontent.com/zephyrproject-rtos/zephyr/master/scripts/requirements.txt && \
	pip3 install -r ${ZEPHYR_BASE}/scripts/requirements.txt && \
    #rm -f requirements.txt && \
	pip3 install sh
RUN pip3 install --user -U west

## Initializing west environment
RUN (cd ${ZEPHYR_BASE}/.. && west init -l ${ZEPHYR_BASE} && west update)

# Setting locales and language
RUN sudo apt-get install -y locales
RUN sudo locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8


# Going to workdirectory
WORKDIR ${APP}
COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY . .

# Building and installing zeta-cli
RUN python3 setup.py sdist bdist_wheel 
RUN cd dist/ && pip3 install *.whl && cd ../

CMD ["/docker-entrypoint.sh"]
