#!/usr/bin/python3
# TODO: Criar os warnings nos arquivos gerados

from ._version import __version__
import yaml
import os
import argparse
import sys
from os import getcwd
from string import Template
import shutil
from pathlib import Path
import re

ZETA_DIR = "."
ZETA_TEMPLATES_DIR = "."
PROJECT_DIR = "."
ZETA_SRC_DIR = "."
ZETA_INCLUDE_DIR = "."


class YamlRefLoader(yaml.SafeLoader):
    def __init__(self, stream):
        super(YamlRefLoader, self).__init__(stream)

    def ref(self, node):
        return self.construct_scalar(node)


class Channel(object):
    def __init__(self,
                 name,
                 initial_value=None,
                 validate='NULL',
                 pre_read='NULL',
                 read='__zt_channel_read_private',
                 pos_read='NULL',
                 pre_publish='NULL',
                 publish='__zt_channel_publish_private',
                 pos_publish='NULL',
                 size=1,
                 persistent=0):
        self.name = name.strip()
        self.validate = validate
        self.pre_read = pre_read
        self.read = read
        self.pos_read = pos_read
        self.pre_publish = pre_publish
        self.publish = publish
        self.pos_publish = pos_publish
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
    def __init__(self,
                 name,
                 priority=10,
                 stack_size=512,
                 sub_channels=[],
                 pub_channels=[]):
        self.name = name
        self.priority = priority
        self.stack_size = stack_size
        self.pub_channels_names = pub_channels
        self.sub_channels_names = sub_channels
        self.pub_channels_obj = []
        self.sub_channels_obj = []


class Config(object):
    def __init__(self,
                 sector_size='DT_FLASH_ERASE_BLOCK_SIZE',
                 sector_count=4,
                 storage_offset='DT_FLASH_AREA_STORAGE_OFFSET',
                 storage_sleep_time=30):
        self.sector_size = sector_size
        self.sector_count = sector_count
        self.storage_offset = storage_offset
        self.storage_sleep_time = storage_sleep_time


class Zeta(object):
    def __init__(self, yamlfile):
        YamlRefLoader.add_constructor('!ref', YamlRefLoader.ref)
        yaml_dict = yaml.load(yamlfile, Loader=YamlRefLoader)
        self.config = Config(**yaml_dict['Config'])
        self.channels = []
        for channel_description in yaml_dict['Channels']:
            for name, fields in channel_description.items():
                self.channels.append(Channel(name, **fields))
        self.services = []
        for service_description in yaml_dict['Services']:
            for name, fields in service_description.items():
                self.services.append(Service(name, **fields))
        self.__check_service_channel_relation()

    def __check_service_channel_relation(self):
        for service in self.services:
            for channel_name in service.pub_channels_names:
                for channel in self.channels:
                    if channel.name == channel_name:
                        channel.pub_services_obj.append(service)
                        service.pub_channels_obj.append(channel)
                        break
                else:
                    raise ValueError("Channel {channel_name} does not exists")
            for channel_name in service.sub_channels_names:
                for channel in self.channels:
                    if channel.name == channel_name:
                        channel.sub_services_obj.append(service)
                        service.sub_channels_obj.append(channel)
                        break
                else:
                    raise ValueError("Channel {channel_name} does not exists")

    def __process_file(self, yaml_dict):
        pass


class FileFactory(object):
    def __init__(self,
                 destination_dir,
                 template_file,
                 zeta,
                 destination_file_name=""):
        if destination_file_name:
            self.destination_file = f'{destination_dir}/{destination_file_name}'
        else:
            self.destination_file = f'{destination_dir}/{template_file.replace(".template", "")}'
        self.template_file = f'{ZETA_TEMPLATES_DIR}/{template_file}'
        self.zeta = zeta
        self.substitutions = {}

    def create_substitutions(self):
        pass

    def generate_file(self):
        with open(self.template_file, 'r') as template:
            t = Template(template.read())
            with open(self.destination_file, 'w') as result_file:
                result_file.write(t.substitute(**self.substitutions))

    def run(self):
        self.create_substitutions()
        self.generate_file()


class HeaderFileFactory(FileFactory):
    def __init__(self, template_file, zeta):
        super().__init__(ZETA_INCLUDE_DIR, template_file, zeta)


class SourceFileFactory(FileFactory):
    def __init__(self, template_file, zeta):
        super().__init__(ZETA_SRC_DIR, template_file, zeta)


class ZetaHeader(HeaderFileFactory):
    def __init__(self, zeta):
        super().__init__('zeta.template.h', zeta)
        self.services_reference = ""

    def create_substitutions(self):
        channel_names = ',\n    '.join([
            f"ZT_{channel.name.upper()}_CHANNEL"
            for channel in self.zeta.channels
        ])
        self.substitutions['channels_enum'] = f'''
typedef enum {{
    {channel_names},
    ZT_CHANNEL_COUNT
}} __attribute__((packed)) zt_channel_e;
'''
        for service in self.zeta.services:
            name = service.name
            priority = service.priority
            stack_size = service.stack_size
            self.services_reference += f'''
/* BEGIN {name} SECTION */
extern zt_service_t {name}_service;
#define {name}_TASK_PRIORITY {priority}
#define {name}_STACK_SIZE {stack_size}
/* END {name} SECTION */
'''
        self.substitutions['services_reference'] = self.services_reference
        self.substitutions['storage_sleep_time'] = self.zeta.config.storage_sleep_time


class ZetaSource(SourceFileFactory):
    def __init__(self, zeta):
        super().__init__('zeta.template.c', zeta)
        self.channels_creation = ''
        self.channels_sems = ''
        self.sector_size = ''
        self.sector_count = ''
        self.storage_offset = ''
        self.set_publishers = ''
        self.set_subscribers = ''
        self.arrays_init = ''

    def gen_sems(self):
        self.channels_sems += f'''
/* BEGIN INITIALIZING CHANNEL SEMAPHORES */
'''
        for channel in self.zeta.channels:
            self.channels_sems += f'''
K_SEM_DEFINE({channel.sem}, 1, 1);
'''

        self.channels_sems += f'''
/* END INITIALIZING CHANNEL SEMAPHORES */
'''

    def gen_creation(self):
        channels = ''
        for channel in self.zeta.channels:
            data_alloc = f"static u8_t __{channel.name.lower()}_data[] = {{{', '.join(channel.initial_value)}}};"
            channel.data = f"__{channel.name.lower()}_data"
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
            self.arrays_init += f'''
/* BEGIN {channel.name} CHANNEL INIT ARRAYS */
{data_alloc}
/* END {channel.name} INIT ARRAYS */
'''
            self.set_subscribers += f'''
/* BEGIN {channel.name} SUBSCRIBERS INIT */
    zt_service_t *{name_subscribers}[] = {{{subscribers_alloc}}};
    __zt_channels[{channel.id}].subscribers = {name_subscribers};
/* END {channel.name} SUBSCRIBERS INIT */
'''
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
            self.set_publishers += f'''
/* BEGIN {channel.name} PUBLISHERS INIT */
    zt_service_t *{name_publishers}[] = {channel.publishers};
    __zt_channels[{channel.id}].publishers = {name_publishers};
/* END {channel.name} PUBLISHERS INIT */
'''
            channels += '''
    {{
        .name = "{name}",
        .validate = {validate},
        .pre_read = {pre_read},
        .read = {read},
        .pos_read = {pos_read},
        .pre_publish = {pre_publish},
        .publish = {publish},
        .pos_publish = {pos_publish},
        .size = {size},
        .persistent = {persistent},
        .sem = &{sem},
        .id = {id},
        .data = {data}
    }},\n'''.format(**vars(channel))

        self.channels_creation = f'''
/* BEGIN INITIALIZING CHANNELS */
static zt_channel_t __zt_channels[ZT_CHANNEL_COUNT] = {{
    {channels}
}};
/* END INITIALIZING CHANNELS */
'''

    def gen_nvs_config(self):
        self.sector_size = self.zeta.config.sector_size
        self.sector_count = self.zeta.config.sector_count
        self.storage_offset = self.zeta.config.storage_offset

    def create_substitutions(self):
        self.gen_nvs_config()
        self.gen_sems()
        self.gen_creation()
        self.substitutions['channels_creation'] = self.channels_creation
        self.substitutions['channels_sems'] = self.channels_sems
        self.substitutions['sector_size'] = self.sector_size
        self.substitutions['sector_count'] = self.sector_count
        self.substitutions['storage_offset'] = self.storage_offset
        self.substitutions['set_publishers'] = self.set_publishers
        self.substitutions['set_subscribers'] = self.set_subscribers
        self.substitutions['arrays_init'] = self.arrays_init


class ZetaCustomFunctionsHeader(HeaderFileFactory):
    def __init__(self, zeta):
        super().__init__('zeta_custom_functions.template.h', zeta)
        self.channels_functions = ''

    def create_substitutions(self):
        for channel in self.zeta.channels:
            name = channel.name
            self.channels_functions += f'''
/* BEGIN {name} CHANNEL FUNCTIONS */
'''
            if channel.pre_read is not 'NULL':
                self.channels_functions += f'''
int {channel.pre_read}(zt_channel_e id, u8_t *channel_value, size_t size);
'''
            if channel.pos_read is not 'NULL':
                self.channels_functions += f'''
int {channel.pos_read}(zt_channel_e id, u8_t *channel_value, size_t size);
'''
            if channel.pre_publish is not 'NULL':
                self.channels_functions += f'''
int {channel.pre_publish}(zt_channel_e id, u8_t *channel_value, size_t size);
'''
            if channel.pos_publish is not 'NULL':
                self.channels_functions += f'''
int {channel.pos_publish}(zt_channel_e id, u8_t *channel_value, size_t size);
'''
            if channel.validate is not 'NULL':
                self.channels_functions += f'''
int {channel.validate}(u8_t *data, size_t size);
'''
            self.channels_functions += f'''
/* END {name} CHANNEL FUNCTIONS */
'''
        self.substitutions['custom_functions'] = self.channels_functions


class ZetaCLI(object):
    def __init__(self):
        parser = argparse.ArgumentParser(description='ZETA cli tool',
                                         usage='''zeta <command> [<args>]
    init - for creating the need files.
    gen - for generating the zeta code based on the zeta.yaml file.''')
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def init(self):
        parser = argparse.ArgumentParser(
            description='''Run this command on the project root directory.
It will create the zeta.cmake and the zeta.yaml (if it does not exist) file on the project folder''',
            usage='zeta init')
        project_dir = "."
        args = parser.parse_args(sys.argv[2:])
        global ZETA_DIR
        ZETA_DIR = os.path.dirname(os.path.realpath(__file__))
        global PROJECT_DIR
        PROJECT_DIR = project_dir
        global ZETA_TEMPLATES_DIR
        ZETA_TEMPLATES_DIR = f"{ZETA_DIR}/templates"
        print("[ZETA]: Generating cmake file on", project_dir)
        with open(f'{ZETA_TEMPLATES_DIR}/zeta.template.cmake',
                  'r') as header_template:
            t = header_template.read()
            with open(f'{PROJECT_DIR}/zeta.cmake', 'w') as cmake:
                cmake.write(t)
        if not os.path.exists(f'{PROJECT_DIR}/zeta.yaml'):
            print("[ZETA]: Generating yaml file on", project_dir)
            with open(f'{ZETA_TEMPLATES_DIR}/zeta.template.yaml',
                      'r') as header_template:
                with open(f'{PROJECT_DIR}/zeta.yaml', 'w') as cmake:
                    cmake.write(header_template.read())

    def check(self):
        OK_COLORED = "\033[0;42m \033[1;97mOK \033[0m"
        FAIL_COLORED = "\033[0;41m \033[1;97mFAIL \033[0m"
        parser = argparse.ArgumentParser(
            description=
            '''Run this command to check all the zeta configuration''',
            usage='zeta init')
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
            zeta_cmake_output = f"{OK_COLORED}: zeta.cmake found ({zeta_cmake_path})"
        else:
            zeta_cmake_output = f"{FAIL_COLORED}: zeta.cmake not found"

        zeta_yaml = Path('./zeta.yaml')
        zeta_yaml_path = zeta_yaml.resolve()
        if zeta_yaml.exists():
            zeta_yaml_output = f"{OK_COLORED}: zeta.yaml found ({zeta_yaml_path})"
        else:
            zeta_yaml_output = f"{FAIL_COLORED}: zeta.yaml not found"

        prj_conf = Path('./prj.conf')
        prj_conf_path = prj_conf.resolve()
        if prj_conf.exists():
            with prj_conf.open() as prj_conf_file:
                for line, line_content in enumerate(prj_conf_file.readlines()):
                    # @todo: check it with an regex. Maybe the line is comment out and it will not be true that it is setup ok
                    if "CONFIG_ZETA=y" in line_content:
                        prj_conf_output = f"{OK_COLORED}: CONFIG_ZETA=y added to the prj ({prj_conf_path}:{line + 1})"
                        break
                else:
                    prj_conf_output = f"{FAIL_COLORED}: CONFIG_ZETA=y NOT added to the prj"

        cmakelists = Path('./CMakeLists.txt')
        cmakelists_path = cmakelists.resolve()
        if cmakelists.exists():
            with cmakelists.open() as cmakelists_file:
                for line, line_content in enumerate(
                        cmakelists_file.readlines()):
                    # @todo: check it with an regex. Maybe the line is comment out and it will not be true that it is setup ok
                    if "include(zeta.cmake NO_POLICY_SCOPE)" in line_content:
                        cmakelists_output = f"{OK_COLORED}: zeta.cmake included properly ({cmakelists_path}:{line + 1})"
                        break
                else:
                    cmakelists_output = f"{FAIL_COLORED}: zeta.cmake NOT included properly into the CMakeLists.txt file"
        services_output = ""

        zeta = None
        try:
            with open(f'{PROJECT_DIR}/zeta.yaml', 'r') as f:
                zeta = Zeta(f)
        except FileNotFoundError:
            #  print("[ZETA]: Could not found zeta.yaml file. Maybe it is not a zeta project.")
            pass
        if zeta:
            services_output = "## \033[1;37mServices\033[0m "
            for service_info in zeta.services:
                service = Path(f'{args.src_dir}',
                               f"{service_info.name.lower()}.c")
                service_path = service.resolve()
                service_init_output = f"        - {FAIL_COLORED}: Service {service_info.name} was NOT initialized properly into the {service_path.name} file"
                service_included_output = f"\n        - {FAIL_COLORED}: Service {service_info.name} was NOT added to be compiled into the CMakeLists.txt file"
                if service.exists():
                    with service.open() as service_file:
                        for line, line_content in enumerate(
                                service_file.readlines()):
                            # @todo: check it with an regex. Maybe the line is comment out and it will not be true that it is setup ok
                            if f"ZT_SERVICE_INIT({service_info.name}," in line_content:
                                service_init_output = f"        - {OK_COLORED}: Service {service_info.name} was initialized properly ({service_path}:{line + 1})"
                                break
                    cmakelists = Path('./CMakeLists.txt')
                    cmakelists_path = cmakelists.resolve()
                    if cmakelists.exists():
                        with cmakelists.open() as cmakelists_file:
                            # @todo: check it with an regex. Maybe the line is comment out and it will not be true that it is setup ok
                            sources = re.search(
                                'list\(APPEND SOURCES(\s*\n?\".*\"\s*\n?)+\)',
                                cmakelists_file.read()).group()
                            if sources and f"{service_info.name.lower()}.c" in sources:
                                service_included_output = f"\n        - {OK_COLORED}: {service_info.name.lower()}.c added to be compiled at the CMakeLists.txt file"
                            else:
                                service_included_output = f"\n        - {FAIL_COLORED}: {service_info.name.lower()}.c was NOT added to be compiled at the CMakeLists.txt file"
                else:
                    service_init_output = f"        - {FAIL_COLORED}: Service {service_info.name} file was NOT found"
                    service_included_output = ""
                services_output += f"""
    {service_info.name}
{service_init_output}{service_included_output}"""
        print(f'''
 \033[1;37mZeta project configuration check\033[0m
===================================================
## \033[1;37mZeta files\033[0m
    - {zeta_cmake_output}
    - {zeta_yaml_output}
## \033[1;37mZephyr setup\033[0m
    - {prj_conf_output}
    - {cmakelists_output}
{services_output}
''')

    def services(self):
        parser = argparse.ArgumentParser(
            description='Verify or create services files on the src folder',
            usage='zeta services [-g] <src dir>')
        parser.add_argument(
            '-g',
            '--generate',
            action='store_true',
            help=
            'Generate services minimal implementation on the [src_dir] directory',
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
        global ZETA_DIR
        ZETA_DIR = os.path.dirname(os.path.realpath(__file__))
        global PROJECT_DIR
        PROJECT_DIR = project_dir
        global ZETA_TEMPLATES_DIR
        ZETA_TEMPLATES_DIR = f"{ZETA_DIR}/templates"
        zeta = None
        with open(f'{PROJECT_DIR}/zeta.yaml', 'r') as f:
            zeta = Zeta(f)
        services_sources = []
        for service in zeta.services:
            service_name = service.name.strip().lower()
            services_sources.append(
                f'"{str(Path("${CMAKE_CURRENT_LIST_DIR}/", f"{args.src_dir}", f"{service_name}.c"))}"'
            )
            if args.generate:
                if not os.path.exists(f'{args.src_dir}/{service_name}.c'):
                    try:
                        service_file = FileFactory(args.src_dir,
                                                   "zeta_service.template_c",
                                                   zeta, f"{service_name}.c")
                        service_file.substitutions[
                            'service_name'] = service.name.upper()
                        service_file.run()
                        print(
                            f"[ZETA]: Generating service {service_name}.c file on the folder {args.src_dir}"
                        )
                    except FileNotFoundError:
                        print(
                            f"[ZETA ERROR]: Failed to generate service files. Destination folder {args.src_dir} does not exists."
                        )
                        return
            else:
                """@todo: check implementations on the src folder (maybe in the future)"""
                pass
        if len(services_sources) > 0:
            cmake_services_file = FileFactory(
                ".", "zeta_with_services.template.cmake", zeta, f"zeta.cmake")
            cmake_services_file.substitutions['services_sources'] = " ".join(
                services_sources)
            cmake_services_file.run()
            print(f"[ZETA]: Inject services sources into the zeta.cmake file")

    def gen(self):
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
            global ZETA_DIR
            ZETA_DIR = os.path.dirname(os.path.realpath(__file__))
            print("[ZETA]: ZETA_DIR =", ZETA_DIR)
            global PROJECT_DIR
            PROJECT_DIR = args.build_dir
            print("[ZETA]: PROJECT_DIR =", PROJECT_DIR)
            global ZETA_SRC_DIR
            ZETA_SRC_DIR = f"{PROJECT_DIR}/zeta/src"
            print("[ZETA]: ZETA_SRC_DIR =", ZETA_SRC_DIR)
            global ZETA_INCLUDE_DIR
            ZETA_INCLUDE_DIR = f"{PROJECT_DIR}/zeta/include"
            print("[ZETA]: ZETA_INCLUDE_DIR =", ZETA_INCLUDE_DIR)
            global ZETA_TEMPLATES_DIR
            ZETA_TEMPLATES_DIR = f"{ZETA_DIR}/templates"
            print("[ZETA]: ZETA_TEMPLATES_DIR =", ZETA_TEMPLATES_DIR)

            try:
                os.makedirs(PROJECT_DIR)
            except FileExistsError as fe_error:
                pass

            try:
                print("[ZETA]: Creating Zeta project folder")
                shutil.copytree(f"{ZETA_TEMPLATES_DIR}/zeta",
                                f"{PROJECT_DIR}/zeta")
            except FileExistsError as fe_error:
                pass

            YamlRefLoader.add_constructor('!ref', YamlRefLoader.ref)
            with open(args.yamlfile, 'r') as f:
                zeta = Zeta(f)
                print("[ZETA]: Generating zeta.h...", end="")
                ZetaHeader(zeta).run()
                print("[OK]")
                print("[ZETA]: Generating zeta.c...", end="")
                ZetaSource(zeta).run()
                print("[OK]")
                print("[ZETA]: Generating zeta_custom_functions.c...", end="")
                ZetaCustomFunctionsHeader(zeta).run()
                print("[OK]")
        else:
            print("[ZETA]: Error. Zeta YAML file does not exist!")


def run():
    ZetaCLI()


if __name__ == "__main__":
    ZetaCLI()
