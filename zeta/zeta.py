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


class ZetaHeader:
    def __init__(self, yaml_dict):
        self.channels = yaml_dict['Channels']
        self.configs = yaml_dict['Config']
        self.channels_enum = f''

    def gen_enum(self):
        channels_names_list = list()
        for c in self.channels:
            name = list(c.keys())[0]
            channels_names_list.append("ZETA_" + name + "_CHANNEL")
        channel_names = ',\n    '.join([f'{x}' for x in channels_names_list])
        self.channels_enum = f'''
typedef enum {{
    {channel_names},
    ZETA_CHANNEL_COUNT
}} __attribute__((packed)) zeta_channel_e;'''

    def gen_file(self):
        with open(f'{ZETA_TEMPLATES_DIR}/zeta.template.h',
                  'r') as header_template:
            t = Template(header_template.read())
            with open(f'{ZETA_INCLUDE_DIR}/zeta.h', 'w') as header:
                header.write(t.substitute(channels_enum=self.channels_enum))

    def run(self):
        self.gen_enum()
        self.gen_file()


class ZetaSource:
    def __init__(self, yaml_dict):
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
                sem = "zeta_" + k + "_channel_sem"
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
                set = "zeta_channel_set_private"
                pos_set = "NULL"
                pre_get = "NULL"
                pos_get = "NULL"
                get = "zeta_channel_get_private"
                size = v['size']
                data_list = list()
                data_list = ["0xFF" for i in range(0, size)]
                persistent = "0"
                subscribers = "NULL"
                data_init = ""
                subscribers_init = ""
                publishers_init = "{NULL}"
                name_data = k + "_data"
                name_subscribers = k + "_subscribers"
                name_publishers = k + "_publishers"

                # Getting name
                name = k
                # Getting sem
                sem = "zeta_" + k + "_channel_sem"
                # Getting ID
                id = "ZETA_" + k + "_CHANNEL"
                # Getting data
                if 'initial_value' in v:
                    data_list = [
                        "0x{:02X}".format(x) for x in v['initial_value']
                    ]
                data_init = "u8_t " + name_data + "[] = {" + ", ".join(
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
                    pass
                # Getting callbacks
                if 'subscribers' in v:
                    subscribers_list = list()
                    for s in v['subscribers']:
                        subscribers_list.append(s['name'] +
                                                "_service_callback")
                    subscribers_init = "zeta_callback_f " + name_subscribers + "[] = { " + ", ".join(
                        subscribers_list) + ", NULL };"
                    subscribers = name_subscribers
                if 'publishers' in v:
                    publishers_list = list()
                    for p in v['publishers']:
                        publishers_list.append(p['name'] + "_thread_id")
                        pass
                    publishers_init = "{ " + ", ".join(
                        publishers_list) + ", NULL }"
                    pass
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
    __zeta_channels[{id}].publishers_id = {name_publishers};
'''
        self.set_publishers += f'''
/* END SET CHANNEL PUBLISHERS */
'''
        self.channels_creation = f'''
static zeta_channel_t __zeta_channels[ZETA_CHANNEL_COUNT] = {{
    {channels}
}};                
'''

    def gen_nvs_config(self):
        self.sector_size = self.config['nvs_sector_size']
        self.sector_count = self.config['nvs_sector_count']
        self.storage_offset = self.config['nvs_storage_offset']

    def gen_file(self):
        with open(f'{ZETA_TEMPLATES_DIR}/zeta.template.c',
                  'r') as source_template:
            s = Template(source_template.read())
            with open(f'{ZETA_SRC_DIR}/zeta.c', 'w') as source:
                source.write(
                    s.substitute(channels_creation=self.channels_creation,
                                 channels_sems=self.channels_sems,
                                 nvs_sector_size=self.sector_size,
                                 nvs_sector_count=self.sector_count,
                                 nvs_storage_offset=self.storage_offset,
                                 arrays_init=self.arrays_init,
                                 set_publishers=self.set_publishers))
        pass

    def run(self):
        self.gen_nvs_config()
        self.gen_sems()
        self.gen_creation()
        self.gen_file()


class ZetaCallbacks:
    def __init__(self, yaml_dict):
        self.services = yaml_dict['Services']
        self.services_callbacks = f''''''
        pass

    def gen_callbacks(self):
        callbacks = f''''''
        for s in self.services:
            for k, v in s.items():
                name_function = k + "_service_callback"
                self.services_callbacks += f'''
void {name_function}(zeta_channel_e id);
'''

    def run(self):
        self.gen_callbacks()
        self.gen_file()

    def gen_file(self):
        with open(f'{ZETA_TEMPLATES_DIR}/zeta_callbacks.template.h',
                  'r') as header_template:
            t = Template(header_template.read())
            with open(f'{ZETA_INCLUDE_DIR}/zeta_callbacks.h', 'w') as header:
                header.write(
                    t.substitute(services_callbacks=self.services_callbacks))


class ZetaThreadHeader:
    def __init__(self, yaml_dict):
        self.services = yaml_dict['Services']
        self.services_sections = f''''''

    def gen_threads_header(self):
        for s in self.services:
            for k, v in s.items():
                name = v['name']
                name_tid = v['name'] + "_thread_id"
                name_thread = v['name'] + "_task"
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

    def gen_file(self):
        with open(f'{ZETA_TEMPLATES_DIR}/zeta_threads.template.h',
                  'r') as header_template:
            t = Template(header_template.read())
            with open(f'{ZETA_INCLUDE_DIR}/zeta_threads.h', 'w') as header:
                header.write(
                    t.substitute(services_sections=self.services_sections))

    def run(self):
        self.gen_threads_header()
        self.gen_file()


class ZetaThreadSource:
    def __init__(self, yaml_dict):
        self.services = yaml_dict['Services']
        self.services_threads = f''''''

    def gen_threads_source(self):
        for s in self.services:
            for k, v in s.items():
                name = v['name']
                name_tid = v['name'] + "_thread_id"
                name_thread = v['name'] + "_task"
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

    def gen_file(self):
        with open(f'{ZETA_TEMPLATES_DIR}/zeta_threads.template.c',
                  'r') as source_template:
            s = Template(source_template.read())
            with open(f'{ZETA_SRC_DIR}/zeta_threads.c', 'w') as source:
                source.write(
                    s.substitute(services_threads=self.services_threads))

    def run(self):
        self.gen_threads_source()
        self.gen_file()


class ZetaCustomFunctions:
    def __init__(self, yaml_dict):
        self.channels = yaml_dict['Channels']
        self.channels_functions = f''''''
        pass

    def gen_custom_functions(self):
        for c in self.channels:
            for k, v in c.items():
                name = k
                self.channels_functions += f'''
/* BEGIN {name} CHANNEL FUNCTIONS */
'''
                if 'pre_get' in v:
                    pre_get_name = v['pre_get']
                    self.channels_functions += f'''
int {pre_get_name}(zeta_channel_e id, u8_t *channel_value, size_t size);
'''
                    pass
                if 'pos_get' in v:
                    pos_get_name = v['pos_get']
                    self.channels_functions += f'''
int {pos_get_name}(zeta_channel_e id, u8_t *channel_value, size_t size);
'''
                    pass
                if 'pre_set' in v:
                    pre_set_name = v['pre_set']
                    self.channels_functions += f'''
int {pre_set_name}(zeta_channel_e id, u8_t *channel_value, size_t size);
'''
                if 'pos_set' in v:
                    pos_set_name = v['pos_set']
                    self.channels_functions += f'''
int {pos_set_name}(zeta_channel_e id, u8_t *channel_value, size_t size);
'''
                    pass
                if 'validate' in v:
                    validate_name = v['validate']
                    self.channels_functions += f'''
int {validate_name}(u8_t *data, size_t size);
'''
                self.channels_functions += f'''
/* END {name} CHANNEL FUNCTIONS */
'''

    def gen_file(self):
        with open(f'{ZETA_TEMPLATES_DIR}/zeta_custom_functions.template.h',
                  'r') as header_template:
            t = Template(header_template.read())
            with open(f'{ZETA_INCLUDE_DIR}/zeta_custom_functions.h',
                      'w') as header:
                header.write(
                    t.substitute(custom_functions=self.channels_functions))

    def run(self):
        self.gen_custom_functions()
        self.gen_file()


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
            'project_dir',
            type=str,
            help='The project root folder where the files will be generated',
            default=".")
        args = parser.parse_args(sys.argv[2:])
        global ZETA_DIR
        ZETA_DIR = os.path.dirname(os.path.realpath(__file__))
        global PROJECT_DIR
        PROJECT_DIR = args.project_dir
        global ZETA_TEMPLATES_DIR
        ZETA_TEMPLATES_DIR = f"{ZETA_DIR}/templates"
        print("Zeta >> Generating cmake file on", args.project_dir)
        with open(f'{ZETA_TEMPLATES_DIR}/zeta.template.cmake',
                  'r') as header_template:
            t = header_template.read()
            with open(f'{PROJECT_DIR}/zeta.cmake', 'w') as cmake:
                cmake.write(t)
        if not os.path.exists(f'{PROJECT_DIR}/zeta.yaml'):
            print("Zeta >> Generating yaml file on", args.project_dir)
            with open(f'{ZETA_TEMPLATES_DIR}/zeta.template.yaml',
                      'r') as header_template:
                with open(f'{PROJECT_DIR}/zeta.yaml', 'w') as cmake:
                    cmake.write(header_template.read())

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
            print("*********************************************")
            print("*              ZETA GENERATION              *")
            print("*********************************************")
            print(os.getcwd())
            global ZETA_DIR
            ZETA_DIR = os.path.dirname(os.path.realpath(__file__))
            print(ZETA_DIR)
            global PROJECT_DIR
            PROJECT_DIR = args.build_dir
            print(PROJECT_DIR)
            global ZETA_SRC_DIR
            ZETA_SRC_DIR = f"{PROJECT_DIR}/zeta/src"
            print(ZETA_SRC_DIR)
            global ZETA_INCLUDE_DIR
            ZETA_INCLUDE_DIR = f"{PROJECT_DIR}/zeta/include"
            print(ZETA_INCLUDE_DIR)
            global ZETA_TEMPLATES_DIR
            ZETA_TEMPLATES_DIR = f"{ZETA_DIR}/templates"
            print(ZETA_TEMPLATES_DIR)

            try:
                os.makedirs(PROJECT_DIR)
            except FileExistsError as fe_error:
                pass

            try:
                print("[ZETA]: creating Zeta project folder")
                shutil.copytree(f"{ZETA_TEMPLATES_DIR}/zeta",
                                f"{PROJECT_DIR}/zeta")
            except FileExistsError as fe_error:
                pass

            with open(args.yamlfile, 'r') as f:
                yaml_dict = yaml.load(f, Loader=yaml.FullLoader)
                print("[ZETA]: generating zeta.h...[OK]")
                ZetaHeader(yaml_dict).run()
                print("[ZETA]: generating zeta.c...[OK]")
                ZetaSource(yaml_dict).run()
                print("[ZETA]: generating zeta_callbacks.c...[OK]")
                ZetaCallbacks(yaml_dict).run()
                print("[ZETA]: generating zeta_threads.h...[OK]")
                ZetaThreadHeader(yaml_dict).run()
                print("[ZETA]: generating zeta_threads.c...[OK]")
                ZetaThreadSource(yaml_dict).run()
                print("[ZETA]: generating zeta_custom_functions.c...[OK]")
                ZetaCustomFunctions(yaml_dict).run()
        else:
            print(" Zeta >> ERROR >> File does not exists!")


def run():
    ZetaCLI()


if __name__ == "__main__":
    ZetaCLI()
