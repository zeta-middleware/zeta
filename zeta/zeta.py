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


class FileFactory(object):
    def __init__(self,
                 destination_dir,
                 template_file,
                 yaml_dict,
                 destination_file_name=""):
        if destination_file_name:
            self.destination_file = f'{destination_dir}/{destination_file_name}'
        else:
            self.destination_file = f'{destination_dir}/{template_file.replace(".template", "")}'
        self.template_file = f'{ZETA_TEMPLATES_DIR}/{template_file}'
        self.yaml_dict = yaml_dict
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
    def __init__(self, template_file, yaml_dict):
        super().__init__(ZETA_INCLUDE_DIR, template_file, yaml_dict)


class SourceFileFactory(FileFactory):
    def __init__(self, template_file, yaml_dict):
        super().__init__(ZETA_SRC_DIR, template_file, yaml_dict)


class ZetaHeader(HeaderFileFactory):
    def __init__(self, yaml_dict):
        super().__init__('zeta.template.h', yaml_dict)

    def create_substitutions(self):
        self.channels = self.yaml_dict['Channels']
        self.configs = self.yaml_dict['Config']
        channels_names_list = list()
        for c in self.channels:
            name = list(c.keys())[0]
            channels_names_list.append(f"ZT_{name}_CHANNEL")
        channel_names = ',\n    '.join([f'{x}' for x in channels_names_list])
        self.substitutions['channels_enum'] = f'''
typedef enum {{
    {channel_names},
    ZT_CHANNEL_COUNT
}} __attribute__((packed)) zt_channel_e;
'''


class ZetaSource(SourceFileFactory):
    def __init__(self, yaml_dict):
        super().__init__('zeta.template.c', yaml_dict)
        self.channels = yaml_dict['Channels']
        self.config = yaml_dict['Config']
        self.channels_creation = f''''''
        self.channels_sems = f''''''
        self.sector_size = f''''''
        self.sector_count = f''''''
        self.storage_offset = f''''''
        self.arrays_init = f''''''
        self.set_publishers = f'''
/* BEGIN SET CHANNEL PUBLISHERS */
'''

    def gen_sems(self):
        self.channels_sems += f'''
/* BEGIN INITIALIZING CHANNEL SEMAPHORES */
'''
        for c in self.channels:
            for k, v in c.items():
                sem = "zt_" + k + "_channel_sem"
                self.channels_sems += f'''
K_SEM_DEFINE({sem}, 1, 1);
'''

        self.channels_sems += f'''
/* END INITIALIZING CHANNEL SEMAPHORES */
'''

    def gen_creation(self):
        channels = f''''''
        for c in self.channels:
            for k, v in c.items():
                validate = "NULL"
                pre_set = "NULL"
                set = "zt_channel_set_private"
                pos_set = "NULL"
                pre_get = "NULL"
                pos_get = "NULL"
                get = "zt_channel_get_private"
                size = v['size']
                data_list = list()
                data_list = ["0xFF" for i in range(0, size)]
                persistent = "0"
                subscribers = "NULL"
                data_init = ""
                subscribers_init = ""
                publishers_init = "{NULL}"
                name_data = f"{k}_data"
                name_subscribers = f"{k}_subscribers"
                name_publishers = f"{k}_publishers"

                # Getting name
                name = k
                # Getting sem
                sem = f"zt_{k}_channel_sem"
                # Getting ID
                id = f"ZT_{k}_CHANNEL"
                # Getting data
                if 'initial_value' in v:
                    data_list = [
                        "0x{:02X}".format(x) for x in v['initial_value']
                    ]
                data_init = f"u8_t {name_data}[] = {{" + ", ".join(
                    data_list) + "};"
                data = name_data
                # Getting validate
                if 'validate' in v:
                    validate = v['validate']
                # Getting set functions
                if 'set' in v and v['set'] == 'NULL':
                    set = 'NULL'
                if 'pre_set' in v:
                    pre_set = v['pre_set']
                if 'pos_set' in v:
                    pos_set = v['pos_set']
                # Getting get function
                if 'get' in v and v['get'] == 'NULL':
                    get = 'NULL'
                if 'pre_get' in v:
                    pre_get = v['pre_get']
                if 'pos_get' in v:
                    pos_get = v['pos_get']
                # Getting persistent
                if 'persistent' in v and v['persistent']:
                    persistent = "1"

                # Getting callbacks
                if 'subscribers' in v:
                    subscribers_list = list()
                    for s in v['subscribers']:
                        s_k = list(s.keys())[0]
                        subscribers_list.append(f"{s_k}_service_callback")
                    subscribers_init = f"zt_callback_f {name_subscribers}[] = {{ " + f", ".join(
                        subscribers_list) + ", NULL };"
                    subscribers = name_subscribers
                if 'publishers' in v:
                    publishers_list = list()
                    for p in v['publishers']:
                        p_k = list(p.keys())[0]
                        publishers_list.append(f"{p_k}_thread_id")
                    publishers_init = "{ " + ", ".join(
                        publishers_list) + ", NULL }"
                self.arrays_init += f'''
/* BEGIN {name} INIT ARRAYS */
{data_init}
{subscribers_init}
/* END {name} INIT ARRAYS */
'''

                channels += f'''
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
        .subscribers_cbs = {subscribers},
        .id = {id},
        .data = {data}
    }},\n'''

                self.set_publishers += f'''
    const k_tid_t {name_publishers}[] = {publishers_init};
    __zt_channels[{id}].publishers_id = {name_publishers};
'''
        self.set_publishers += f'''
/* END SET CHANNEL PUBLISHERS */
'''
        self.channels_creation = f'''
static zt_channel_t __zt_channels[ZT_CHANNEL_COUNT] = {{
    {channels}
}};                
'''

    def gen_nvs_config(self):
        self.sector_size = self.config['nvs_sector_size']
        self.sector_count = self.config['nvs_sector_count']
        self.storage_offset = self.config['nvs_storage_offset']

    def create_substitutions(self):
        self.gen_nvs_config()
        self.gen_sems()
        self.gen_creation()
        self.substitutions['channels_creation'] = self.channels_creation
        self.substitutions['channels_sems'] = self.channels_sems
        self.substitutions['nvs_sector_size'] = self.sector_size
        self.substitutions['nvs_sector_count'] = self.sector_count
        self.substitutions['nvs_storage_offset'] = self.storage_offset
        self.substitutions['arrays_init'] = self.arrays_init
        self.substitutions['set_publishers'] = self.set_publishers


class ZetaCallbacksHeader(HeaderFileFactory):
    def __init__(self, yaml_dict):
        super().__init__('zeta_callbacks.template.h', yaml_dict)
        self.services = yaml_dict['Services']
        self.services_callbacks = f''''''

    def create_substitutions(self):
        callbacks = f''''''
        for s in self.services:
            for k, v in s.items():
                name_function = f"{k}_service_callback"
                self.services_callbacks += f'''
void {name_function}(zt_channel_e id);
'''
        self.substitutions['services_callbacks'] = self.services_callbacks


class ZetaThreadHeader(HeaderFileFactory):
    def __init__(self, yaml_dict):
        super().__init__('zeta_threads.template.h', yaml_dict)
        self.services = yaml_dict['Services']
        self.services_sections = f''''''

    def create_substitutions(self):
        for s in self.services:
            for k, v in s.items():
                name = k
                name_tid = f"{k}_thread_id"
                name_thread = f"{k}_task"
                priority = v['priority']
                stack_size = v['stack_size']
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
    def __init__(self, yaml_dict):
        super().__init__('zeta_threads.template.c', yaml_dict)
        self.services = yaml_dict['Services']
        self.services_threads = f''''''

    def create_substitutions(self):
        for s in self.services:
            for k, v in s.items():
                name = k
                name_tid = f"{k}_thread_id"
                name_thread = f"{k}_task"
                priority = v['priority']
                stack_size = v['stack_size']
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
    def __init__(self, yaml_dict):
        super().__init__('zeta_custom_functions.template.h', yaml_dict)
        self.channels = yaml_dict['Channels']
        self.channels_functions = f''''''

    def create_substitutions(self):
        for c in self.channels:
            for k, v in c.items():
                name = k
                self.channels_functions += f'''
/* BEGIN {name} CHANNEL FUNCTIONS */
'''
                if 'pre_get' in v:
                    pre_get_name = v['pre_get']
                    self.channels_functions += f'''
int {pre_get_name}(zt_channel_e id, u8_t *channel_value, size_t size);
'''
                if 'pos_get' in v:
                    pos_get_name = v['pos_get']
                    self.channels_functions += f'''
int {pos_get_name}(zt_channel_e id, u8_t *channel_value, size_t size);
'''
                if 'pre_set' in v:
                    pre_set_name = v['pre_set']
                    self.channels_functions += f'''
int {pre_set_name}(zt_channel_e id, u8_t *channel_value, size_t size);
'''
                if 'pos_set' in v:
                    pos_set_name = v['pos_set']
                    self.channels_functions += f'''
int {pos_set_name}(zt_channel_e id, u8_t *channel_value, size_t size);
'''
                if 'validate' in v:
                    validate_name = v['validate']
                    self.channels_functions += f'''
int {validate_name}(u8_t *data, size_t size);
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
                                    'service_name'] = service
                                service_file.run()
                                print(
                                    f"[ZETA]: Generating service {service}.c file on the folder {args.gen_services}"
                                )
                            except FileNotFoundError:
                                print(
                                    f"[ZETA ERROR]: Failed to generate service files. Destination folder {args.gen_services} does not exists."
                                )
                                return

    def mount_subscribers_publishers(self, dic):
        channels = dic['Channels']
        services = dic['Services']
        services_names_set = set()
        map_services_names_to_array = dict()
        id = 0
        for s in services:
            key = list(s.keys())[0]
            map_services_names_to_array[key] = id
            id += 1
        for c in channels:
            for k, v in c.items():
                if 'subscribers' in v:
                    subscribers_mounted = list()
                    for s in v['subscribers']:
                        subscribers_mounted.append(
                            services[map_services_names_to_array[s]])
                        v['subscribers'] = subscribers_mounted
                if 'publishers' in v:
                    publishers_mounted = list()
                    for p in v['publishers']:
                        publishers_mounted.append(
                            services[map_services_names_to_array[p]])
                        v['publishers'] = publishers_mounted

    def construct_yaml(self, f):
        yaml_dict = yaml.load(f, Loader=YamlRefLoader)
        self.mount_subscribers_publishers(yaml_dict)
        return yaml_dict

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
                yaml_dict = self.construct_yaml(f)
                print("[ZETA]: Generating zeta.h...", end="")
                ZetaHeader(yaml_dict).run()
                print("[OK]")
                print("[ZETA]: Generating zeta.c...", end="")
                ZetaSource(yaml_dict).run()
                print("[OK]")
                print("[ZETA]: Generating zeta_callbacks.c...", end="")
                ZetaCallbacksHeader(yaml_dict).run()
                print("[OK]")
                print("[ZETA]: Generating zeta_threads.h...", end="")
                ZetaThreadHeader(yaml_dict).run()
                print("[OK]")
                print("[ZETA]: Generating zeta_threads.c...", end="")
                ZetaThreadSource(yaml_dict).run()
                print("[OK]")
                print("[ZETA]: Generating zeta_custom_functions.c...", end="")
                ZetaCustomFunctionsHeader(yaml_dict).run()
                print("[OK]")
        else:
            print("[ZETA]: Error. Zeta YAML file does not exist!")


def run():
    ZetaCLI()


if __name__ == "__main__":
    ZetaCLI()
