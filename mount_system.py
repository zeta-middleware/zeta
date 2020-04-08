import yaml
import os
from os import getcwd
from string import Template

class PdbHeader :
    def __init__(self, yaml_dict) :
        self.channels = yaml_dict['Channels']
        self.channels_enum = f''

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
        
    def gen(self):
        with open('templates/pdb.template.h', 'r') as header_template :
            t = Template(header_template.read())
            with open('build/zephyr/include/generated/pdb.h', 'w') as header :
                header.write(t.substitute(channels_enum=self.channels_enum))

    def run(self) :
        self.gen_enum()
        self.gen()

class PdbSource :
    def __init__(self, yaml_dict) :
        self.channels = yaml_dict['Channels']
        self.channels_creation = f''
        self.channels_sems = f''''''

    def gen_sems(self) :
        for c in self.channels :
            for k, v in c.items() :
                sem = "pdb_" + k + "_channel_sem"
                self.channels_sems += f'''
K_SEM_DEFINE({sem}, 1, 1);
'''
    def gen_creation(self) :
        channels = f''''''
        for c in self.channels :
            for k, v in c.items() :
                validate = "NULL"
                pre_set = "NULL"
                set = "pdb_channel_set_private"
                pos_set = "NULL"
                get = "pdb_channel_get_private"
                size = v['size']
                data_list = list()
                data_list = ["0xFF" for i in range(0, size)]
                persistent = "0"
                subscribers = "NULL"
                publishers = "NULL"
                
                # Getting name
                name = "PDB_" + k + "_CHANNEL"
                # Getting sem
                sem = "pdb_" + k + "_channel_sem"
                # Getting ID
                id = name
                # Getting data
                if 'initial_value' in v :
                    data_list = ["0x{:02X}".format(x) for x in v['initial_value']]
                data = "{" + ", ".join(data_list)  + "}"
                # Getting validate
                if 'validate' in v :
                    validate = v['validate']
                # Getting set functions
                if 'pre_set' in v :
                    pre_set = v['pre_set']
                if 'set' in v :
                    set = v['set']
                if 'pos_set' in v :
                    pos_set = v['pos_set']
                # Getting get function
                if 'get' in v :
                    get = v['get']
                # Getting persistent
                if 'persistent' in v and v['persistent'] :
                    persistent = "1"
                    pass
                # Getting callbacks
                if 'subscribers' in v :
                    subscribers_list = list()
                    for s in v['subscribers'] :
                        subscribers_list.append(s['name'] + "_service_callback")
                    subscribers = "{ " + ", ".join(subscribers_list) + ", NULL }"
                if 'publishers' in v :
                    publishers_list = list()
                    for p in v['publishers'] :
                        publishers_list.append(p['name'] + "_thread_id")
                    publishers = "{ " + ", ".join(publishers_list)  + ", NULL }"
                    pass

                channels += f'''
    {{
        .name = "{name}",       
        .validate = {validate},
        .get = {get},
        .pre_set = {pre_set},
        .set = {set},
        .pos_set = {pos_set},
        .size = {size},
        .persistent = {persistent},
        .changed = 0,
        .sem = &{sem},
        .publishers_id = {publishers},
        .subscribers_cbs = {subscribers},
        .id = {name},
        .data = {data}
    }},\n'''
                
        self.channels_creation = f'''
static pdb_channel_t __pdb_channels[PDB_CHANNEL_COUNT] = {{
    {channels}
}};                
'''
    def gen(self) :
        with open('templates/pdb.template.c', 'r') as source_template :
            s = Template(source_template.read())
            with open('build/zephyr/src/generated/pdb.c', 'w') as source :
                source.write(s.substitute(channels_creation=self.channels_creation, channels_sems=self.channels_sems))
        pass
    
    def run(self) :
        self.gen_sems()
        self.gen_creation()
        self.gen()


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
        self.gen()

    def gen(self) :
        with open('templates/pdb_callbacks.template.h', 'r') as header_template :
            t = Template(header_template.read())
            with open('build/zephyr/include/generated/pdb_callbacks.h', 'w') as header :
                header.write(t.substitute(services_callbacks=self.services_callbacks))

def main() :
    try :
        os.makedirs('build/zephyr/src/generated')
    except FileExistsError as fe_error:
        print("[MESSAGE]: Skip creation of zephyr/src/generated folder")
        
    with open('properties.yaml', 'r') as f:
        yaml_dict = yaml.load(f, Loader=yaml.FullLoader)
        PdbHeader(yaml_dict).run()
        PdbSource(yaml_dict).run()
        PdbCallbacks(yaml_dict).run()
    
if __name__ == "__main__":
    main()
