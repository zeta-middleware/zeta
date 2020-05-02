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
                 pre_get='NULL',
                 get='zt_channel_get_private',
                 pos_get='NULL',
                 pre_set='NULL',
                 set='zt_channel_set_private',
                 pos_set='NULL',
                 size=1,
                 persistent=0):
        self.name = name.strip()
        self.validate = validate
        self.pre_get = pre_get
        self.get = get
        self.pos_get = pos_get
        self.pre_set = pre_set
        self.set = set
        self.pos_set = pos_set
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
                 nvs_sector_size='DT_FLASH_ERASE_BLOCK_SIZE',
                 nvs_sector_count=4,
                 nvs_storage_offset='DT_FLASH_AREA_STORAGE_OFFSET'):
        self.nvs_sector_size = nvs_sector_size
        self.nvs_sector_count = nvs_sector_count
        self.nvs_storage_offset = nvs_storage_offset


class Zeta(object):
    def __init__(self, yamlfile):
        YamlRefLoader.add_constructor('!ref', YamlRefLoader.ref)
        yaml_dict = yaml.load(yamlfile, Loader=YamlRefLoader)
        self.config = Config(**yaml_dict['Config'])
        self.channels = []
        for channel_description in yaml_dict['Channels']:
            for name, fields in  channel_description.items():
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


class ZetaSource(SourceFileFactory):
    def __init__(self, zeta):
        super().__init__('zeta.template.c', zeta)
        self.channels_creation = ''
        self.channels_sems = ''
        self.sector_size = ''
        self.sector_count = ''
        self.storage_offset = ''
        self.arrays_init = ''
        self.set_publishers = ''

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
            channel.data = f"(u8_t []){{{', '.join(channel.initial_value)}}}"
            channel.subscribers_cbs = "NULL"
            if len(channel.sub_services_obj) > 0:
                channel.subscribers_cbs = [
                    f"{service.name}_service_callback"
                    for service in channel.sub_services_obj
                ]
                channel.subscribers_cbs.append('NULL')
                channel.subscribers_cbs = ', '.join(channel.subscribers_cbs)
            channel.subscribers_cbs = f"(zt_callback_f[]){{{channel.subscribers_cbs}}}"

            channel.publishers_id = "NULL"
            if len(channel.pub_services_obj) > 0:
                channel.publishers_id = [
                    f"{service.name}_thread_id"
                    for service in channel.pub_services_obj
                ]
                channel.publishers_id.append("NULL")
                channel.publishers_id = ', '.join(channel.publishers_id)
            channel.publishers_id = f"{{{channel.publishers_id}}}"

            name_publishers = f"{channel.name.lower()}_publishers"
            self.set_publishers += f'''
    const k_tid_t {name_publishers}[] = {channel.publishers_id};
    __zt_channels[{channel.id}].publishers_id = {name_publishers};
'''
            channels += '''
    {{
        .name = "{name}",       
        .validate = {validate},
        .pre_get = {pre_get},
        .get = {get},
        .pos_get = {pos_get},
        .pre_set = {pre_set},
        .set = {set},
        .pos_set = {pos_set},
        .size = {size},
        .persistent = {persistent},
        .sem = &{sem},
        .subscribers_cbs = {subscribers_cbs},
        .id = {id},
        .data = {data}
    }},\n'''.format(**vars(channel))

        self.channels_creation = f'''
static zt_channel_t __zt_channels[ZT_CHANNEL_COUNT] = {{
    {channels}
}};                
'''
    def gen_nvs_config(self):
        self.sector_size = self.zeta.config.nvs_sector_size
        self.sector_count = self.zeta.config.nvs_sector_count
        self.storage_offset = self.zeta.config.nvs_storage_offset

    def create_substitutions(self):
        self.gen_nvs_config()
        self.gen_sems()
        self.gen_creation()
        self.substitutions['channels_creation'] = self.channels_creation
        self.substitutions['channels_sems'] = self.channels_sems
        self.substitutions['nvs_sector_size'] = self.sector_size
        self.substitutions['nvs_sector_count'] = self.sector_count
        self.substitutions['nvs_storage_offset'] = self.storage_offset
        self.substitutions['set_publishers'] = self.set_publishers


class ZetaCallbacksHeader(HeaderFileFactory):
    def __init__(self, zeta):
        super().__init__('zeta_callbacks.template.h', zeta)
        self.services_callbacks = ''

    def create_substitutions(self):
        callbacks = ''
        for service in self.zeta.services:
            self.services_callbacks += f'''
void {service.name}_service_callback(zt_channel_e id);
'''
        self.substitutions['services_callbacks'] = self.services_callbacks


class ZetaThreadHeader(HeaderFileFactory):
    def __init__(self, zeta):
        super().__init__('zeta_threads.template.h', zeta)
        self.services_sections = ''

    def create_substitutions(self):
        for service in self.zeta.services:
            name = service.name
            name_tid = f"{name}_thread_id"
            name_thread = f"{name}_task"
            priority = service.priority
            stack_size = service.stack_size
            self.services_sections += f'''
/* BEGIN {name} SECTION */
void {name_thread}(void);
extern const k_tid_t {name_tid};
#define {name}_TASK_PRIORITY {priority}
#define {name}_STACK_SIZE {stack_size}
/* END {name} SECTION */
'''
        self.substitutions['services_sections'] = self.services_sections


class ZetaThreadSource(SourceFileFactory):
    def __init__(self, zeta):
        super().__init__('zeta_threads.template.c', zeta)
        self.services_threads = ''

    def create_substitutions(self):
        for service in self.zeta.services:
            name = service.name
            name_tid = f"{name}_thread_id"
            name_thread = f"{name}_task"
            priority = service.priority
            stack_size = service.stack_size
            self.services_threads += f'''
/* BEGIN {name} THREAD DEFINE */
K_THREAD_DEFINE({name_tid},
                {stack_size},
                {name_thread},
                NULL, NULL, NULL,
                {priority},
                0,
                K_NO_WAIT
                );
/* END {name} THREAD DEFINE */                
'''
        self.substitutions['services_threads'] = self.services_threads


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
            if channel.pre_get is not 'NULL':
                self.channels_functions += f'''
int {channel.pre_get}(zt_channel_e id, u8_t *channel_value, size_t size);
'''
            if channel.pos_get is not 'NULL':
                self.channels_functions += f'''
int {channel.pos_get}(zt_channel_e id, u8_t *channel_value, size_t size);
'''
            if channel.pre_set is not 'NULL':
                self.channels_functions += f'''
int {channel.pre_set}(zt_channel_e id, u8_t *channel_value, size_t size);
'''
            if channel.pos_set is not 'NULL':
                self.channels_functions += f'''
int {channel.pos_set}(zt_channel_e id, u8_t *channel_value, size_t size);
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
            description='Create zeta.cmake file on the project folder',
            usage='zeta init <project dir>')
        # prefixing the argument with -- means it's optional
        parser.add_argument(
            '-s',
            '--gen_services',
            nargs='?',
            const="./src",
            type=str,
            help=
            'Generate services minimal implementation on the directory pass as arg',
        )
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
            print("[ZETA]: Generating yaml file on", args.project_dir)
            with open(f'{ZETA_TEMPLATES_DIR}/zeta.template.yaml',
                      'r') as header_template:
                with open(f'{PROJECT_DIR}/zeta.yaml', 'w') as cmake:
                    cmake.write(header_template.read())
        if args.gen_services:
            with open(f'{PROJECT_DIR}/zeta.yaml', 'r') as f:
                YamlRefLoader.add_constructor('!ref', YamlRefLoader.ref)
                yaml_dict = yaml.load(f, Loader=YamlRefLoader)
                for s in yaml_dict['Services']:
                    for service in s.keys():
                        service = service.strip().lower()
                        if not os.path.exists(
                                f'{args.gen_services}/{service}.c'):
                            try:
                                service_file = FileFactory(
                                    args.gen_services,
                                    "zeta_service.template.c", yaml_dict,
                                    f"{service}.c")
                                service_file.substitutions[
                                    'service_name'] = service.upper()
                                service_file.run()
                                print(
                                    f"[ZETA]: Generating service {service}.c file on the folder {args.gen_services}"
                                )
                            except FileNotFoundError:
                                print(
                                    f"[ZETA ERROR]: Failed to generate service files. Destination folder {args.gen_services} does not exists."
                                )
                                return

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
                #  yaml_dict = self.construct_yaml(f)
                print("[ZETA]: Generating zeta.h...", end="")
                ZetaHeader(zeta).run()
                print("[OK]")
                print("[ZETA]: Generating zeta.c...", end="")
                ZetaSource(zeta).run()
                print("[OK]")
                print("[ZETA]: Generating zeta_callbacks.c...", end="")
                ZetaCallbacksHeader(zeta).run()
                print("[OK]")
                print("[ZETA]: Generating zeta_threads.h...", end="")
                ZetaThreadHeader(zeta).run()
                print("[OK]")
                print("[ZETA]: Generating zeta_threads.c...", end="")
                ZetaThreadSource(zeta).run()
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
