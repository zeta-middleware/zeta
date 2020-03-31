#!/usr/bin/env python3

import yaml
from os import getcwd

class PropertyCreateGeneration :
    def __init__(self) :
        self.properties_create = ""
        self.validators_def = ""
        self.callbacks = ""
        self.observers_def = ""
        self.observers_check = ""
        self.properties_initial_value = ""

    def generate_queues(self, obs) :
        ret = list()
        for o in obs :
            ret.append('&' + o['name'] + '_event_queue')
        return ', '.join(ret)
        # l = [ x.strip() for x in obs.split('|')]
        # for i in range(0, len(l)) :
        #     l[i] = 'PDB_' + l[i] + '_MODULE'
        # return ' | '.join(l)

    def generate_property_create(self, p) :
        self.properties_create += "PDB_PROPERTY_CREATE("
        # getting property name
        name = list(p.keys())[0]

        # getting property size
        nbytes = p[name]['nbytes'] if 'nbytes' in p[name] else 1

        # getting set function
        set = p[name]['set'] if 'set' in p[name] else 'pdb_property_set_private'
        if set != 'NULL' and set != 'pdb_property_set_private' :
            self.callbacks += 'int ' + set + '(pdb_property_e id, u8_t *property_value, size_t size);\n'

        self.properties_initial_value += 'PDB_PROPERTIES_INITIAL_VALUE(' + name + ', ' + str(nbytes) + ', '
        arr = '0'
        if 'initial_value' in p[name] :
            if len(p[name]['initial_value']) == nbytes :
                arr = ', '.join(['0x{:02X}'.format(x) for x in p[name]['initial_value']])
            else :
                exit(5)
                pass
            pass
        self.properties_initial_value += arr + ')\n'

        if set == 'NULL' and not ('initial_value' in p[name]) :
            exit(5)
                
        # getting validate function
        validate = p[name]['validate'] if 'validate' in p[name] else 'NULL'
        if validate != 'NULL' and validate != 'pdb_validator_different_of_zero' :
            self.validators_def += 'int ' + validate + '(u8_t *property_value, size_t size);\n'

        # getting get function
        get = p[name]['get'] if 'get' in p[name] else 'pdb_property_get_private'
        if get != 'NULL' and get != 'pdb_property_get_private' :
            self.callbacks += 'int ' + get + '(pdb_property_e id, u8_t *property_value, size_t size);\n'

        # getting persistency
        if ('persistent' in p[name]) :
            in_flash = '1' if p[name]['persistent'] == True else '0'
        else :
            in_flash = '0'

        # getting observers
        if ('observers' in p[name]) :
            queues = self.generate_queues(p[name]['observers'])
            observers = str(len(p[name]['observers']))
            out = [name, str(nbytes), validate, get, set, in_flash, observers, name, queues]
        else :
            observers = '0'
            out = [name, str(nbytes), validate, get, set, in_flash, observers, name, 'NULL']

        # mounting output macro create
        self.properties_create += ', '.join(out) + ')\n'

    def generate_observers(self, obs) :
        for d in obs :
            o = list(d.values())[0]
            self.observers_def += 'PDB_OBSERVER_CREATE(' + o['name'] + ', ' + str(o['event_queue_size']) + ')\n'
            if 'diy' in o and o['diy'] == False :
                self.observers_check += 'PDB_OBSERVER_THREAD_CREATE(' + o['name'] + ', ' + str(o['thread_size']) + ', ' + str(o['thread_priority']) + ', ' + o['event_callback'] + ');\n'

    def run(self) :
        with open('../properties.yaml', 'r') as file:
            yaml_dict = yaml.load(file, Loader=yaml.FullLoader)
            properties = yaml_dict['Properties']
            observers = yaml_dict['Observers']
            self.generate_observers(observers)
            for p in properties :
                self.generate_property_create(p)
            with open('zephyr/include/generated/pdb_properties.def', 'w') as f :
                f.write(self.properties_create)
            with open('zephyr/include/generated/pdb_validators.def', 'w') as f :
                f.write(self.validators_def)
            with open('zephyr/include/generated/pdb_callbacks.def', 'w') as f :
                f.write(self.callbacks)
            with open('zephyr/include/generated/pdb_observers.def', 'w') as f :
                f.write(self.observers_def)
            with open('zephyr/include/generated/pdb_observers_thread.def', 'w') as f :
                f.write(self.observers_check)
            with open('zephyr/include/generated/pdb_properties_initial_value.def', 'w') as f :
                f.write(self.properties_initial_value)                

def main():
    pcg = PropertyCreateGeneration()
    pcg.run()

if __name__ == "__main__":
    main()
