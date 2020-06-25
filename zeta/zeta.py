#!/usr/bin/python3

import argparse
import os
import re
import shutil
import subprocess
import sys
import textwrap
import traceback
from pathlib import Path
from string import Template

import yaml

from _io import TextIOWrapper

from ._version import __version__
from .zeta_errors import *

ZETA_MODULE_DIR = "."
ZETA_TEMPLATES_DIR = "."
PROJECT_DIR = "."
ZETA_DIR = "."
ZETA_SRC_DIR = "."
ZETA_INCLUDE_DIR = "."


class ZetaYamlLoader(yaml.SafeLoader):
    """Modifies the SafeLoader object and generates a correct
    dictionary-based in the YAML file.
    """
    def __init__(self, stream):
        """YamlRefloader constructor.

        :param stream: default param used for yaml.SafeLoader
        :returns: None
        :rtype: None

        """
        super(ZetaYamlLoader, self).__init__(stream)

    def ref(self, node):
        """Handles ref statements in YAML file and generate a valid
        reference

        :param node: Ref statement with the reference name
        :returns: Reference name
        :rtype: str

        """
        return self.construct_scalar(node)

    def include(self, node):
        """Handles include statements in YAML file and generate a
        valid reference

        :param node: Include statement with the reference name
        :returns: Content of the file passed by include
        :rtype: dict

        """
        include_yaml = dict()
        path = f"{PROJECT_DIR}/../{self.construct_scalar(node)}" if PROJECT_DIR != "." else f"{self.construct_scalar(node)}"
        with open(path, "r") as f:
            include_yaml = yaml.load(f, Loader=ZetaYamlLoader)
        return include_yaml


class Channel(object):
    """Represents a channel written on YAML file.
    """
    def __init__(self,
                 name: str,
                 initial_value: list = None,
                 read_only: bool = False,
                 on_changed: bool = False,
                 size: int = 1,
                 persistent: int = 0) -> None:
        """Channel constructor.

        :param name: Channel name
        :param initial_value: Initial value assigned to channel
        :param read_only: Allows publish operations or not
        :param on_changed: Defines the callback call procedure after a
        publish operation
        :param size: Channel size
        :param persistent: Defines if the channel that must be saved on
        flash
        :returns: None
        :rtype: None

        """
        self.name = name.strip()
        self.read_only = int(read_only)
        self.on_changed = int(on_changed)
        self.size = size
        self.persistent = 1 if persistent else 0
        self.sem = f"zt_{name.lower()}_channel_sem"
        self.id = f"ZT_{name.upper()}_CHANNEL"
        self.initial_value = initial_value
        if initial_value is None:
            self.initial_value = [hex(x) for x in [0] * self.size]
        else:
            self.initial_value = [hex(x) for x in initial_value]

        self.pub_services_obj = []
        self.sub_services_obj = []


class Service(object):
    """Represents a service written on YAML file.
    """
    def __init__(self,
                 name: str,
                 priority: int = 10,
                 stack_size: int = 512,
                 sub_channels: list = [],
                 pub_channels: list = []) -> None:
        """Service constructor.

        :param name: Service name
        :param priority: Defines the service priority
        :param stack_size: Defines the service stack size
        :param sub_channels: Assigns all channels that service must be
        subscribed
        :param pub_channels: Assigns all channels that service must be
        published
        :returns: None
        :rtype: None

        """
        self.name = name
        self.priority = priority
        self.stack_size = stack_size
        self.pub_channels_names = pub_channels
        self.sub_channels_names = sub_channels
        self.pub_channels_obj = []
        self.sub_channels_obj = []


class Config(object):
    def __init__(self,
                 sector_count: int = 4,
                 storage_partition: str = 'storage',
                 storage_period: int = 30) -> None:
        """Config constructor.

        :param sector_count: Sector count that must be used
        :param storage_partition: Defines the storage partition that must be
        used to save channel data
        :param storage_period: Defines the period that zeta will be save
        channel data pending
        :returns: None
        :rtype: None

        """
        self.sector_count = sector_count
        self.storage_partition = storage_partition
        self.storage_period = storage_period


class Zeta(object):
    """Represents the Zeta object that has access to services, channels
    and config parameters specified in YAML file.
    """
    def __init__(self, yamlfile: TextIOWrapper) -> None:
        """Zeta constructor.

        :param yamlfile: Zeta yaml file config
        :returns: None
        :rtype: None
        :raise ZetaCLIError: Error creating Channel object or Service object

        """
        ZetaYamlLoader.add_constructor('!ref', ZetaYamlLoader.ref)
        ZetaYamlLoader.add_constructor('!include', ZetaYamlLoader.include)
        yaml_dict = yaml.load(yamlfile, Loader=ZetaYamlLoader)
        try:
            self.config = Config(**yaml_dict['Config'])
        except KeyError:
            self.config = Config()
        self.channels = []
        for channel_description in yaml_dict['Channels']:
            for name, fields in channel_description.items():
                try:
                    self.channels.append(Channel(name, **fields))
                except TypeError as terr:
                    raise ZetaCLIError(
                        f"Error creating Channel object. {terr.__str__()}",
                        EZTFIELD)
        self.services = []
        for service_description in yaml_dict['Services']:
            for name, fields in service_description.items():
                try:
                    self.services.append(Service(name, **fields))
                except TypeError as terr:
                    raise ZetaCLIError(
                        f"Error creating Service object. {terr.__str__()}",
                        EZTFIELD)
        self.__check_service_channel_relation()

    def __check_service_channel_relation(self) -> None:
        """Checks if the use of !ref is correct or is used some
        nonexistent channel.

        :returns: None
        :rtype: None
        :raise ZetaCLIError: Channel name doesn't exists in channel list.

        """
        for service in self.services:
            for channel_name in service.pub_channels_names:
                for channel in self.channels:
                    if channel.name == channel_name:
                        channel.pub_services_obj.append(service)
                        service.pub_channels_obj.append(channel)
                        break
                else:
                    raise ZetaCLIError(
                        f"Channel {channel_name} does not exists", EZTINVREF)
            for channel_name in service.sub_channels_names:
                for channel in self.channels:
                    if channel.name == channel_name:
                        channel.sub_services_obj.append(service)
                        service.sub_channels_obj.append(channel)
                        break
                else:
                    raise ZetaCLIError(
                        f"Channel {channel_name} does not exists", EZTINVREF)

    def __process_file(self, yaml_dict: dict):
        """Continues the processing of yamfile

        :param yaml_dict: Dictionary derived by yamlfile
        :returns: None
        :rtype: None

        """
        pass


class FileFactory(object):
    """Represents a generic class responsible to generate a file-based
    in a template and your respective substitutions.
    """
    def __init__(self,
                 destination_dir: str,
                 template_file: str,
                 zeta: Zeta,
                 destination_file_name: str = "") -> None:
        """FileFactory constructor.

        :param destination_dir: The directory where the generated file
        will be saved
        :param template_file: Template file
        :param zeta: Zeta object
        :param destination_file_name: The file name that will be saved
        :returns: None
        :rtype: None

        """
        if destination_file_name:
            self.destination_file = (
                f"{destination_dir}/{destination_file_name}")
        else:
            self.destination_file = (
                f'{destination_dir}/{template_file.replace(".template", "")}')
        self.template_file = f'{ZETA_TEMPLATES_DIR}/{template_file}'
        self.zeta = zeta
        self.substitutions = {}

    def create_substitutions(self) -> None:
        """The function that will be implemented by classes inherited.

        :returns: None
        :rtype: None

        """
        pass

    def generate_file(self) -> None:
        """Writes the output file with the respective substitutions
        assigned in create_substitutions function.

        :returns: None
        :rtype: None

        """
        with open(self.template_file, 'r') as template:
            t = Template(template.read())
            with open(self.destination_file, 'w') as result_file:
                result_file.write(t.substitute(**self.substitutions))

    def run(self) -> None:
        """Runs the routine responsible for assigns substitutions and
        write the output file.

        :returns: None
        :rtype: None

        """
        self.create_substitutions()
        self.generate_file()


class HeaderFileFactory(FileFactory):
    """Represents a generic class for creation of header files that will
    be used by Zeta.
    """
    def __init__(self, template_file: str, zeta: Zeta) -> None:
        """Headerfilefactory constructor.

        :param template_file: Template file
        :param zeta: Zeta object
        :returns: None
        :rtype: None

        """
        super().__init__(ZETA_INCLUDE_DIR, template_file, zeta)


class SourceFileFactory(FileFactory):
    """Represents a generic class for creation of source files that will
    be used by Zeta.
    """
    def __init__(self, template_file: str, zeta: Zeta) -> None:
        """SourceFilefactory constructor.

        :param template_file: Template file
        :param zeta: Zeta object
        :returns: None
        :rtype: None

        """
        super().__init__(ZETA_SRC_DIR, template_file, zeta)


class ZetaConf(FileFactory):
    def __init__(self, zeta: Zeta) -> None:
        super().__init__(ZETA_DIR, "zeta.template.conf", zeta)

    def create_substitutions(self):
        storage = "n"
        for channel in self.zeta.channels:
            if channel.persistent:
                storage = "y"
                break
        else:
            print("[ZETA]: Zeta storage disabled")
        self.substitutions['storage'] = storage


class ZetaHeader(HeaderFileFactory):
    """Represents a class that generates the zeta.h file and has the
    goal to assigns all the substitutions needed to Zeta works
    properly.
    """
    def __init__(self, zeta: Zeta) -> None:
        """ZetaHeader constructor.

        :param zeta: Zeta object
        :returns: None
        :rtype: None

        """
        super().__init__('zeta.template.h', zeta)
        self.services_reference = ""
        self.max_channel_size = 0

    def create_substitutions(self) -> None:
        """Responsible for assigns the needed substitutions to be
        written on the output file.

        :returns: None
        :rtype: None

        """
        service_names = ',\n   '.join([
            f"ZT_{service.name.upper()}_SERVICE"
            for service in self.zeta.services
        ])
        self.substitutions['services_enum'] = textwrap.dedent('''
        typedef enum {{
            {service_names},
            ZT_SERVICE_COUNT
        }} __attribute__((packed)) zt_service_e;
        ''').format(service_names=service_names)

        channel_names = ',\n    '.join([
            f"ZT_{channel.name.upper()}_CHANNEL"
            for channel in self.zeta.channels
        ])
        self.substitutions['channels_enum'] = textwrap.dedent('''
            typedef enum {{
                {channel_names},
                ZT_CHANNEL_COUNT
            }} __attribute__((packed)) zt_channel_e;
            ''').format(channel_names=channel_names)
        for service in self.zeta.services:
            name = service.name
            priority = service.priority
            stack_size = service.stack_size
            self.services_reference += textwrap.dedent(f'''
                /* BEGIN {name} SECTION */
                extern zt_service_t {name}_service;
                #define {name}_TASK_PRIORITY {priority}
                #define {name}_STACK_SIZE {stack_size}
                /* END {name} SECTION */
                ''')

        for channel in self.zeta.channels:
            self.max_channel_size = max(self.max_channel_size, channel.size)

        self.substitutions['services_reference'] = self.services_reference
        self.substitutions['storage_period'] = self.zeta.config.storage_period
        self.substitutions['max_channel_size'] = str(self.max_channel_size)


class ZetaSource(SourceFileFactory):
    """Represents a class that generates the zeta.c file and has the
    goal to assigns all the substitutions needed to Zeta works
    properly.
    """
    def __init__(self, zeta: Zeta) -> None:
        """ZetaSource constructor.

        :param zeta: Zeta object
        :returns: None
        :rtype: None

        """
        super().__init__('zeta.template.c', zeta)
        self.channels_creation = ''
        self.channels_sems = ''
        self.sector_size = ''
        self.sector_count = ''
        self.storage_offset = ''
        self.set_publishers = ''
        self.set_subscribers = ''
        self.arrays_init = ''
        self.services_array_init = ''

    def gen_sems(self) -> None:
        """Responsible for assigns the channel semaphores.

        :returns: None
        :rtype: None

        """
        self.channels_sems += textwrap.dedent('''
            /* BEGIN INITIALIZING CHANNEL SEMAPHORES */
            ''')
        for channel in self.zeta.channels:
            self.channels_sems += textwrap.dedent(f'''
                K_SEM_DEFINE({channel.sem}, 1, 1);
                ''')

        self.channels_sems += textwrap.dedent('''
            /* END INITIALIZING CHANNEL SEMAPHORES */
            ''')

    def gen_creation(self) -> None:
        """Responsible for creates all the channels that will be used by
        Zeta.

        :returns: None
        :rtype: None

        """
        channels = ''
        services_list = list()
        for service in self.zeta.services:
            services_list.append(f'&{service.name}_service')
        services_joined = ', '.join(services_list)
        self.services_array_init = textwrap.dedent(f'''
        zt_service_t *__zt_services[ZT_SERVICE_COUNT] = {{{services_joined}}};
        ''')
        for channel in self.zeta.channels:
            data_alloc = (f"static u8_t __{channel.name.lower()}_data[] ="
                          f"{{{', '.join(channel.initial_value)}}};")
            channel.data = f"__{channel.name.lower()}_data"
            channel.flag = 0x00
            if channel.on_changed:
                channel.flag = channel.flag | (1 << 2)

            subscribers_alloc = "NULL"
            if len(channel.sub_services_obj) > 0:
                subscribers_alloc = [
                    f"&{service.name}_service"
                    for service in channel.sub_services_obj
                ]
                subscribers_alloc.append('NULL')
                subscribers_alloc = ', '.join(subscribers_alloc)
            name_subscribers = f"{channel.name.lower()}_subscribers"
            channel.subscribers = f"__{channel.name.lower()}_subcribers"
            self.arrays_init += textwrap.dedent(f'''
                /* BEGIN {channel.name} CHANNEL INIT ARRAYS */
                {data_alloc}
                /* END {channel.name} INIT ARRAYS */
                ''')
            self.set_subscribers += textwrap.dedent(f'''
                /* BEGIN {channel.name} SUBSCRIBERS INIT */
                    zt_service_t *{name_subscribers}[] = {{{subscribers_alloc}}};
                    __zt_channels[{channel.id}].subscribers = {name_subscribers};
                /* END {channel.name} SUBSCRIBERS INIT */
                ''')
            channel.publishers = "NULL"
            if len(channel.pub_services_obj) > 0:
                channel.publishers = [
                    f"&{service.name}_service"
                    for service in channel.pub_services_obj
                ]
                channel.publishers.append("NULL")
                channel.publishers = ', '.join(channel.publishers)
            channel.publishers = f"{{{channel.publishers}}}"

            name_publishers = f"{channel.name.lower()}_publishers"
            self.set_publishers += textwrap.dedent(f'''
                /* BEGIN {channel.name} PUBLISHERS INIT */
                    zt_service_t *{name_publishers}[] = {channel.publishers};
                    __zt_channels[{channel.id}].publishers = {name_publishers};
                /* END {channel.name} PUBLISHERS INIT */
                ''')
            channels += textwrap.indent(
                '''
                {{
                    .name = "{name}",
                    .read_only = {read_only},
                    .flag = {{.data = {flag}}},
                    .size = {size},
                    .persistent = {persistent},
                    .sem = &{sem},
                    .id = {id},
                    .data = {data}
                }},\n'''.format(**vars(channel)), '')

        self.channels_creation = textwrap.dedent(f'''
            /* BEGIN INITIALIZING CHANNELS */
            static zt_channel_t __zt_channels[ZT_CHANNEL_COUNT] = {{
                {channels}
            }};
            /* END INITIALIZING CHANNELS */
            ''')

    def gen_nvs_config(self) -> None:
        """Responsible for assigns the nvs config.

        :returns: None
        :rtype: None

        """
        self.sector_count = self.zeta.config.sector_count
        self.storage_partition = self.zeta.config.storage_partition

    def create_substitutions(self) -> None:
        """Responsible for assigns the needed substitutions to be written
        on the output file.

        :returns: None
        :rtype: None

        """
        self.gen_nvs_config()
        self.gen_sems()
        self.gen_creation()
        self.substitutions['channels_creation'] = self.channels_creation
        self.substitutions['channels_sems'] = self.channels_sems
        self.substitutions['sector_count'] = self.sector_count
        self.substitutions['storage_partition'] = self.storage_partition
        self.substitutions['set_publishers'] = self.set_publishers
        self.substitutions['set_subscribers'] = self.set_subscribers
        self.substitutions['arrays_init'] = self.arrays_init
        self.substitutions['services_array_init'] = self.services_array_init


class ZetaCLI(object):
    """Represents the ZetaCLI and has all the callbacks that will be
    called when the user type zeta on the terminal.
    """
    def __init__(self) -> None:
        """ZetaCLI constructor.

        :returns: None
        :rtype: None

        """
        parser = argparse.ArgumentParser(
            description='ZETA cli tool',
            usage=
            (f"zeta <command> [<args>]\r\nCommands\r\n"
             f"  init - for creating the need files.\r\n"
             f"  gen - for generating the zeta code based on the zeta.yaml file.\r\n"
             f"  check -  for checking the needed configuration and initialization of zeta.\r\n"
             f"  services - for generating the code-template based for services defined on the zeta.yaml file.\r\n"
             f"  version - for getting the current ZetaCLI version."))
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        exit(getattr(self, args.command)())

    def init(self) -> int:
        """Called when the user type "zeta init" and is responsible for
        generates the minimum requirements in order to Zeta works
        properly.

        :returns: Exit code
        :rtype: int
        :raise ZetaCLIError: Error in zeta.cmake or zeta.yaml file path

        """
        argparse.ArgumentParser(
            description='''Run this command on the project root directory.
            It will create the zeta.cmake and the zeta.yaml files''',
            usage='zeta init')
        project_dir = "."
        global ZETA_MODULE_DIR
        ZETA_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
        global PROJECT_DIR
        PROJECT_DIR = project_dir
        global ZETA_TEMPLATES_DIR
        ZETA_TEMPLATES_DIR = f"{ZETA_MODULE_DIR}/templates"

        try:
            zeta_yaml_path = Path(f'{PROJECT_DIR}/zeta.yaml')
            if not zeta_yaml_path.exists():
                with open(f'{ZETA_TEMPLATES_DIR}/zeta.template.yaml',
                          'r') as header_template:
                    with zeta_yaml_path.open(mode='w') as zeta_yaml:
                        zeta_yaml.write(header_template.read())
                print("[ZETA]: Generating yaml file on", project_dir)
        except FileNotFoundError:
            raise ZetaCLIError(
                "Error in such file or directory related to zeta.yaml",
                EZTFILE)
        zeta = None
        zeta_yaml_path = Path('./zeta.yaml')
        if zeta_yaml_path.exists():
            with zeta_yaml_path.open() as zeta_yaml:
                zeta = Zeta(zeta_yaml)
        try:
            cmake_file = FileFactory(".", "zeta.template.cmake", zeta,
                                     "zeta.cmake")
            cmake_file.substitutions['services_sources'] = ""
            cmake_file.run()
            print("[ZETA]: Generating cmake file on", project_dir)
        except FileNotFoundError:
            raise ZetaCLIError(
                "Failed to generate service files. Error opening and creating zeta.cmake",
                EZTFILE)
        return 0

    def version(self) -> int:
        """Called when the user type "zeta version" and is responsible
        for sends out the ZetaCLI version.

        :returns: Exit code
        :rtype: int

        """
        print(f"ZetaCLI version {__version__}")
        print(f"ZetaCLI is maintained and supported by Zeta-Middleware group.")
        return 0

    def check(self) -> int:
        """Called when the user type "zeta check" and is responsible for
        checks if the needed steps were made by user in order to Zeta
        works properly.

        :returns: Exit code
        :rtype: int

        """
        ecode = 0
        OK_COLORED = "\033[0;42m \033[1;97mOK \033[0m"
        FAIL_COLORED = "\033[0;41m \033[1;97mFAIL \033[0m"
        WARNING_COLORED = "\033[1;43m \033[1;97mWARNING \033[0m"
        parser = argparse.ArgumentParser(
            description=
            '''Run this command to check all the zeta configuration''',
            usage='zeta check')
        parser.add_argument(
            '-s',
            '--src_dir',
            type=str,
            default="./src/",
            help='Services source directory',
        )
        args = parser.parse_args(sys.argv[2:])
        zeta_cmake = Path('./zeta.cmake')
        zeta_cmake_path = zeta_cmake.resolve()
        if zeta_cmake.exists():
            zeta_cmake_output = (
                f" {OK_COLORED} zeta.cmake found ({zeta_cmake_path})")
        else:
            ecode = EZTCHECKFAILED
            zeta_cmake_output = f" {FAIL_COLORED} zeta.cmake not found"

        zeta_yaml = Path('./zeta.yaml')
        zeta_yaml_path = zeta_yaml.resolve()
        if zeta_yaml.exists():
            zeta_yaml_output = (
                f" {OK_COLORED} zeta.yaml found ({zeta_yaml_path})")
        else:
            ecode = EZTCHECKFAILED
            zeta_yaml_output = f" {FAIL_COLORED} zeta.yaml not found"

        cmakelists = Path('./CMakeLists.txt')
        cmakelists_path = cmakelists.resolve()
        if cmakelists.exists():
            with cmakelists.open() as cmakelists_file:
                for line, line_content in enumerate(
                        cmakelists_file.readlines()):
                    # @todo: check it with an regex. Maybe the line is comment
                    # out and it will not be true that it is setup ok
                    if "include(zeta.cmake NO_POLICY_SCOPE)" in line_content:
                        cmakelists_output = (
                            f" {OK_COLORED} zeta.cmake included properly"
                            f" ({cmakelists_path}:{line + 1})")
                        break
                else:
                    ecode = EZTCHECKFAILED
                    cmakelists_output = (
                        f" {FAIL_COLORED} zeta.cmake NOT included properly"
                        " into the CMakeLists.txt file")
        services_output = ""
        services_output_list = []

        zeta = None
        try:
            with open(f'{PROJECT_DIR}/zeta.yaml', 'r') as f:
                zeta = Zeta(f)
        except ZetaCLIError as zerr:
            #  print("[ZETA]: Could not found zeta.yaml file. Maybe it is not a zeta project.")
            pass
        if zeta and zeta_cmake.exists():
            for service_info in zeta.services:
                service = Path(f'{args.src_dir}',
                               f"{service_info.name.lower()}.c")
                service_path = service.resolve()
                ok_hit = 0
                service_init_output = (
                    f" {FAIL_COLORED} Service"
                    f" {service_info.name} was NOT initialized properly into"
                    f" the {service_path.name} file")
                service_included_output = (
                    f"\n {FAIL_COLORED} Service {service_info.name} was NOT"
                    " added to be compiled into the CMakeLists.txt file")
                if service.exists():
                    with service.open() as service_file:
                        for line, line_content in enumerate(
                                service_file.readlines()):
                            # @todo: check it with an regex. Maybe the line is
                            # comment out and it will not be true that it is setup ok
                            if f"ZT_SERVICE_INIT({service_info.name}," in line_content:
                                ok_hit += 1
                                service_init_output = (
                                    f" {OK_COLORED} Service "
                                    f"{service_info.name} was initialized"
                                    f" properly ({service_path}:{line + 1})")
                                break
                    with zeta_cmake.open() as zeta_cmake_file:
                        sources = re.search(
                            r'list\(APPEND SOURCES(\s*\n?\".*\"\s*\n?)+\)',
                            zeta_cmake_file.read())
                        if sources and f"{service_info.name.lower()}.c" in sources.group(
                        ):
                            ok_hit += 1
                            service_included_output = (
                                f"\n {OK_COLORED}"
                                f" {service_info.name.lower()}.c added to be"
                                f" compiled at the zeta.cmake file")
                        else:
                            cmakelists = Path('./CMakeLists.txt')
                            cmakelists_path = cmakelists.resolve()
                            if cmakelists.exists():
                                with cmakelists.open() as cmakelists_file:
                                    sources = re.search(
                                        r'list\(APPEND SOURCES(\s*\n?\".*\"\s*\n?)+\)',
                                        cmakelists_file.read())
                                    if sources and f"{service_info.name.lower()}.c" in sources.group(
                                    ):
                                        ok_hit += 1
                                        service_included_output = (
                                            f"\n {OK_COLORED}"
                                            " {service_info.name.lower()}.c"
                                            " added to be compiled at the"
                                            " CMakeLists.txt file")
                                    else:
                                        service_included_output = (
                                            f"\n {FAIL_COLORED}"
                                            " {service_info.name.lower()}.c"
                                            " was NOT added to be compiled")
                else:
                    service_init_output = (
                        f" {WARNING_COLORED} Service"
                        f" {service_info.name} file was NOT found")
                    service_included_output = ""
                ecode = 0 if ((ecode != EZTCHECKFAILED) and
                              (ok_hit == 2)) else EZTCHECKFAILED
                services_output_list.append(
                    f"""{service_init_output}{service_included_output}""")
        services_output = "\n" + "\n".join(services_output_list)
        check_output = textwrap.dedent(f'''\
                [ZETA]: Zeta project configuration check...
                {zeta_cmake_output}
                {zeta_yaml_output}
                {cmakelists_output}''') + services_output
        print(check_output)
        return ecode

    def services(self) -> int:
        """Called when the user type "zeta services" and is responsible
        for generates files template-based with the services initialized.

        :returns: Exit code
        :rtype: int
        :raise ZetaCLIError: Error opening or reading files

        """
        parser = argparse.ArgumentParser(
            description='Verify or create services files on the src folder',
            usage='zeta services [-g] <src dir>')
        parser.add_argument(
            '-g',
            '--generate',
            action='store_true',
            help=('Generate services minimal implementation'
                  ' on the [src_dir] directory'),
        )
        parser.add_argument(
            '-s',
            '--src_dir',
            type=str,
            default="./src/",
            help='Services source directory',
        )
        project_dir = "."
        args = parser.parse_args(sys.argv[2:])
        global ZETA_MODULE_DIR
        ZETA_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
        global PROJECT_DIR
        PROJECT_DIR = project_dir
        global ZETA_TEMPLATES_DIR
        ZETA_TEMPLATES_DIR = f"{ZETA_MODULE_DIR}/templates"
        zeta = None
        try:
            with open(f'{PROJECT_DIR}/zeta.yaml', 'r') as f:
                zeta = Zeta(f)
        except FileNotFoundError:
            raise ZetaCLIError("Error opening zeta.yaml file, file not found",
                               EZTFILE)
        services_sources = []
        for service in zeta.services:
            service_name = service.name.strip().lower()
            services_sources.append((
                f'"{str(Path("${CMAKE_CURRENT_LIST_DIR}/", f"{args.src_dir}", f"{service_name}.c"))}"'
            ))
            if args.generate:
                if not os.path.exists(f'{args.src_dir}'):
                    os.makedirs(f'{args.src_dir}')
                if not os.path.exists(f'{args.src_dir}/{service_name}.c'):
                    try:
                        service_file = FileFactory(args.src_dir,
                                                   "zeta_service.template_c",
                                                   zeta, f"{service_name}.c")
                        service_file.substitutions[
                            'service_name'] = service.name.upper()
                        service_file.run()
                        print((
                            f"[ZETA]: Generating service {service_name}.c file"
                            f" on the folder {args.src_dir}"))
                    except FileNotFoundError:
                        raise ZetaCLIError(
                            f"Failed to generate service files. Destination folder {args.src_dir} does not exists",
                            EZTFILE)

            else:
                """@todo: check implementations on the src folder (maybe in the future)"""
                pass
        if len(services_sources) > 0:
            try:
                cmake_file = FileFactory(".", "zeta.template.cmake", zeta,
                                         "zeta.cmake")
                cmake_file.substitutions[
                    'services_sources'] = "list(APPEND SOURCES {})".format(
                        " ".join(services_sources))
                cmake_file.run()
                print(
                    "[ZETA]: Inject services sources into the zeta.cmake file")
            except FileNotFoundError:
                raise ZetaCLIError(
                    "Failed to generate service files. Error opening and creating zeta.cmake",
                    EZTFILE)
            return 0

    def gen(self) -> int:
        """Generate all the internal files that represents Zeta system
        like channels, Zeta threads, Zeta API, and others.

        :returns: Exit code
        :rtype: int

        """
        parser = argparse.ArgumentParser(
            description='Generate zeta files on the build folder',
            usage='zeta gen [-p] yamlfile')
        # prefixing the argument with -- means it's optional
        parser.add_argument(
            '-b',
            '--build_dir',
            type=str,
            help='The project root folder where the files will be generated',
            default=".")
        parser.add_argument(
            'yamlfile',
            help='Yaml that must be read in order to mount system.')
        args = parser.parse_args(sys.argv[2:])
        if os.path.exists(args.yamlfile):
            print("[ZETA]: Current dir =", os.getcwd())
            global ZETA_MODULE_DIR
            ZETA_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
            print("[ZETA]: ZETA_MODULE_DIR =", ZETA_MODULE_DIR)
            global PROJECT_DIR
            PROJECT_DIR = args.build_dir
            print("[ZETA]: PROJECT_DIR =", PROJECT_DIR)
            global ZETA_DIR
            ZETA_DIR = f"{PROJECT_DIR}/zeta"
            print("[ZETA]: ZETA_DIR = ", ZETA_DIR)
            global ZETA_SRC_DIR
            ZETA_SRC_DIR = f"{PROJECT_DIR}/zeta/src"
            print("[ZETA]: ZETA_SRC_DIR =", ZETA_SRC_DIR)
            global ZETA_INCLUDE_DIR
            ZETA_INCLUDE_DIR = f"{PROJECT_DIR}/zeta/include"
            print("[ZETA]: ZETA_INCLUDE_DIR =", ZETA_INCLUDE_DIR)
            global ZETA_TEMPLATES_DIR
            ZETA_TEMPLATES_DIR = f"{ZETA_MODULE_DIR}/templates"
            print("[ZETA]: ZETA_TEMPLATES_DIR =", ZETA_TEMPLATES_DIR)

            try:
                os.makedirs(PROJECT_DIR)
            except FileExistsError:
                pass

            try:
                print("[ZETA]: Creating Zeta project folder")
                shutil.copytree(f"{ZETA_TEMPLATES_DIR}/zeta",
                                f"{PROJECT_DIR}/zeta")
            except FileExistsError:
                pass

            with open(args.yamlfile, 'r') as f:
                zeta = Zeta(f)
                print("[ZETA]: Generating zeta.h...", end="")
                ZetaHeader(zeta).run()
                print("[OK]")
                print("[ZETA]: Generating zeta.c...", end="")
                ZetaSource(zeta).run()
                print("[OK]")
                print("[ZETA]: Generating zeta.conf...", end="")
                ZetaConf(zeta).run()
                print("[OK]")
            subprocess.run("zeta check", shell=True)
        else:
            print("[ZETA]: Error. Zeta YAML file does not exist!")
        return 0


def run():
    try:
        ZetaCLI()
    except ZetaCLIError as zterr:
        zterr.handle()
    except Exception as err:
        print(
            f"[ZetaCLI Error] [Code: {EZTUNEXP}]: Unexpected exception ocurred."
        )
        print(traceback.print_exc())
        exit(EZTUNEXP)
