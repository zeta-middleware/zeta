# TODO: Criar os warnings nos arquivos gerados
import yaml
import os
from os import getcwd
from string import Template

class PdbHeader :
    def __init__(self, yaml_dict) :
        self.channels = yaml_dict['Channels']
        self.configs = yaml_dict['Config']
        self.channels_enum = f''
        self.pdb_stack_size = f''
        self.storage_stack_size = f''

    def gen_enum(self) :
        channels_names_list = list()
        for c in self.channels :
            name = list(c.keys())[0]
            channels_names_list.append("PDB_" + name + "_CHANNEL")
        channel_names = ',\n    '.join([f'{x}' for x in channels_names_list])
        self.channels_enum = f'''
typedef enum {{
    {channel_names},
    PDB_CHANNEL_COUNT
}} __attribute__((packed)) pdb_channel_e;'''

    def gen_configs(self) :
        pdb_stack_size = self.configs['pdb_stack_size']
        storage_stack_size = self.configs['storage_stack_size']
        self.pdb_stack_size += f'''{pdb_stack_size}'''
        self.storage_stack_size += f'''{storage_stack_size}'''

    def gen_file(self):
        with open('../templates/pdb.template.h', 'r') as header_template :
            t = Template(header_template.read())
            with open('zephyr/include/generated/pdb.h', 'w') as header :
                header.write(t.substitute(channels_enum=self.channels_enum, storage_stack_size=self.storage_stack_size, pdb_stack_size=self.pdb_stack_size))

    def run(self) :
        self.gen_enum()
        self.gen_configs()
        self.gen_file()

class PdbSource :
    def __init__(self, yaml_dict) :
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

    def gen_sems(self) :
        self.channels_sems += f'''
/* BEGIN INITIALIZING CHANNEL SEMAPHORES */
'''
        for c in self.channels :
            for k, v in c.items() :
                sem = "pdb_" + k + "_channel_sem"
                self.channels_sems += f'''
K_SEM_DEFINE({sem}, 1, 1);
'''

        self.channels_sems += f'''
/* END INITIALIZING CHANNEL SEMAPHORES */
'''

    def gen_creation(self) :
        channels = f''''''
        for c in self.channels :
            for k, v in c.items() :
                validate = "NULL"
                pre_set = "NULL"
                set = "pdb_channel_set_private"
                pos_set = "NULL"
                pre_get = "NULL"
                get = "pdb_channel_get_private"
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
                name = "PDB_" + k + "_CHANNEL"
                # Getting sem
                sem = "pdb_" + k + "_channel_sem"
                # Getting ID
                id = name
                # Getting data
                if 'initial_value' in v :
                    data_list = ["0x{:02X}".format(x) for x in v['initial_value']]
                data_init = "u8_t " + name_data + "[] = {" + ", ".join(data_list)  + "};"
                data = name_data
                # Getting validate
                if 'validate' in v :
                    validate = v['validate']
                # Getting set functions
                if 'set' in v and v['set'] == 'NULL' :
                    set = 'NULL'
                if 'pre_set' in v :
                    pre_set = v['pre_set']
                if 'pos_set' in v :
                    pos_set = v['pos_set']
                # Getting get function
                if 'get' in v and v['get'] == 'NULL' :
                    get = 'NULL'
                if 'pre_get' in v :
                    pre_get = v['pre_get']
                # Getting persistent
                if 'persistent' in v and v['persistent'] :
                    persistent = "1"
                    pass
                # Getting callbacks
                if 'subscribers' in v :
                    subscribers_list = list()
                    for s in v['subscribers'] :
                        subscribers_list.append(s['name'] + "_service_callback")
                    subscribers_init = "pdb_callback_f " + name_subscribers + "[] = { " + ", ".join(subscribers_list) + ", NULL };"
                    subscribers = name_subscribers
                if 'publishers' in v :
                    publishers_list = list()
                    for p in v['publishers'] :
                        publishers_list.append(p['name'] + "_thread_id")
                        pass
                    publishers_list.append("pdb_thread_id")
                    publishers_init = "{ " + ", ".join(publishers_list)  + ", NULL }"
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
        .pre_set = {pre_set},
        .set = {set},
        .pos_set = {pos_set},
        .size = {size},
        .persistent = {persistent},
        .sem = &{sem},
        .subscribers_cbs = {subscribers},
        .id = {name},
        .data = {data}
    }},\n'''

                self.set_publishers += f'''
    const k_tid_t {name_publishers}[] = {publishers_init};
    __pdb_channels[{name}].publishers_id = {name_publishers};
'''
        self.set_publishers += f'''
/* END SET CHANNEL PUBLISHERS */
'''
        self.channels_creation = f'''
static pdb_channel_t __pdb_channels[PDB_CHANNEL_COUNT] = {{
    {channels}
}};                
'''

    def gen_nvs_config(self) :
        self.sector_size = self.config['nvs_sector_size']
        self.sector_count = self.config['nvs_sector_count']
        self.storage_offset = self.config['nvs_storage_offset']

    def gen_file(self) :
        with open('../templates/pdb.template.c', 'r') as source_template :
            s = Template(source_template.read())
            with open('zephyr/src/generated/pdb.c', 'w') as source :
                source.write(s.substitute(channels_creation=self.channels_creation, channels_sems=self.channels_sems, nvs_sector_size=self.sector_size, nvs_sector_count=self.sector_count, nvs_storage_offset=self.storage_offset, arrays_init=self.arrays_init, set_publishers=self.set_publishers))
        pass
    
    def run(self) :
        self.gen_nvs_config()
        self.gen_sems()
        self.gen_creation()
        self.gen_file()


class PdbCallbacks :
    def __init__(self, yaml_dict) :
        self.services = yaml_dict['Services']
        self.services_callbacks = f''''''
        pass

    def gen_callbacks(self) :
        callbacks = f''''''
        for s in self.services :
            for k, v in s.items() :
                name_function = k + "_service_callback"
                self.services_callbacks +=f'''
void {name_function}(pdb_channel_e id);
'''
        
    def run(self) :
        self.gen_callbacks()
        self.gen_file()

    def gen_file(self) :
        with open('../templates/pdb_callbacks.template.h', 'r') as header_template :
            t = Template(header_template.read())
            with open('zephyr/include/generated/pdb_callbacks.h', 'w') as header :
                header.write(t.substitute(services_callbacks=self.services_callbacks))


class PdbThreadHeader :
    def __init__(self, yaml_dict) :
        self.services = yaml_dict['Services']
        self.services_sections = f''''''

    def gen_threads_header(self) :
        for s in self.services :
            for k, v in s.items() :
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
    def gen_file(self) :
        with open('../templates/pdb_threads.template.h', 'r') as header_template :
            t = Template(header_template.read())
            with open('zephyr/include/generated/pdb_threads.h', 'w') as header :
                header.write(t.substitute(services_sections=self.services_sections))
        
    def run(self) :
        self.gen_threads_header()
        self.gen_file()

class PdbThreadSource :
    def __init__(self, yaml_dict) :
        self.services = yaml_dict['Services']
        self.services_threads = f''''''

    def gen_threads_source(self) :
        for s in self.services :
            for k, v in s.items() :
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

    def gen_file(self) :
        with open('../templates/pdb_threads.template.c', 'r') as source_template :
            s = Template(source_template.read())
            with open('zephyr/src/generated/pdb_threads.c', 'w') as source :
                source.write(s.substitute(services_threads=self.services_threads))

    def run(self) :
        self.gen_threads_source()
        self.gen_file()


class PdbCustomFunctions :
    def __init__(self, yaml_dict) :
        self.channels = yaml_dict['Channels']
        self.channels_functions = f''''''
        pass

    def gen_custom_functions(self) :
        for c in self.channels :
            for k, v in c.items() :
                name = k
                self.channels_functions += f'''
/* BEGIN {name} CHANNEL FUNCTIONS */
'''
                if 'pre_get' in v :
                    pre_get_name = v['pre_get']
                    self.channels_functions += f'''
int {pre_get_name}(pdb_channel_e id, u8_t *channel_value, size_t size);
'''
                    pass
                if 'pre_set' in v :
                    pre_set_name = v['pre_set']
                    self.channels_functions += f'''
int {pre_set_name}(pdb_channel_e id, u8_t *channel_value, size_t size);
'''        
                if 'pos_set' in v :
                    pos_set_name = v['pos_set']
                    self.channels_functions += f'''
int {pos_set_name}(pdb_channel_e id, u8_t *channel_value, size_t size);
'''
                    pass
                if 'validate' in v :
                    validate_name = v['validate']
                    self.channels_functions += f'''
int {validate_name}(u8_t *data, size_t size);
'''
                self.channels_functions += f'''
/* END {name} CHANNEL FUNCTIONS */
'''

    def gen_file(self) :
        with open('../templates/pdb_custom_functions.template.h', 'r') as header_template :
            t = Template(header_template.read())
            with open('zephyr/include/generated/pdb_custom_functions.h', 'w') as header :
                header.write(t.substitute(custom_functions=self.channels_functions))

    def run(self) :
        self.gen_custom_functions()
        self.gen_file()
    
def main() :
    try :
        os.makedirs('../build/zephyr/src/generated/')
    except FileExistsError as fe_error:
        print("[PDB]: Skip creation of srs/generated folder")        
        
    with open('../pdb.yaml', 'r') as f:
        yaml_dict = yaml.load(f, Loader=yaml.FullLoader)
        PdbHeader(yaml_dict).run()
        PdbSource(yaml_dict).run()
        PdbCallbacks(yaml_dict).run()
        PdbThreadHeader(yaml_dict).run()
        PdbThreadSource(yaml_dict).run()
        PdbCustomFunctions(yaml_dict).run()
if __name__ == "__main__":
    main()
