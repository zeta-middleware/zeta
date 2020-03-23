#!/usr/bin/env python3

import yaml
from os import getcwd

class PropertyCreateGeneration :
    def __init__(self) :
        self.properties_macro_create = ""
        self.validators_h_create = ""
        self.callbacks_h_create = ""

    def generate_observers(self, obs) :
        l = [ x.strip() for x in obs.split('|')]
        for i in range(0, len(l)) :
            l[i] = 'PDB_' + l[i] + '_MODULE'
        return ' | '.join(l)

    def generate_property_create(self, p) :
        self.properties_macro_create += "PDB_PROPERTY_CREATE("
        # getting property name
        name = list(p.keys())[0]

        # getting property size
        nbytes = p[name]['nbytes'] if 'nbytes' in p[name] else '1'

        # getting set function
        set = p[name]['set'] if 'set' in p[name] else 'pdb_property_set_private'
        if set != 'NULL' and set != 'pdb_property_set_private' :
            self.callbacks_h_create += 'int ' + set + '(pdb_property_e id, u8_t *property_value, size_t size);\n'

        # getting validate function
        validate = p[name]['validate'] if 'validate' in p[name] else 'NULL'
        if validate != 'NULL' and validate != 'pdb_binary' :
            self.validators_h_create += 'int ' + validate + '(u8_t *property_value, size_t size);\n'

        # getting get function
        get = p[name]['get'] if 'get' in p[name] else 'pdb_property_get_private'
        if get != 'NULL' and get != 'pdb_property_get_private' :
            self.callbacks_h_create += 'int ' + get + '(pdb_property_e id, u8_t *property_value, size_t size);\n'

        # getting persistency
        if ('persistent' in p[name]) :
            in_flash = '1' if p[name]['persistent'] == 'true' else '0'
        else :
            in_flash = '0'

        # getting observers
        if ('observers' in p[name]) :
            observers = self.generate_observers(p[name]['observers'])
        else :
            observers = '0'

        # mounting output macro create
        out = [name, nbytes, validate, get, set, in_flash, observers, name]
        self.properties_macro_create += ', '.join(out) + ')\n'

    def run(self) :
        with open('../properties.yaml', 'r') as file:
            properties_dict = yaml.load(file, Loader=yaml.FullLoader)
            properties = properties_dict['Properties']
            print(properties)
            for p in properties :
                self.generate_property_create(p)
            with open('../include/generated/properties.def', 'w') as f :
                f.write(self.properties_macro_create)
            with open('../include/generated/validators.def', 'w') as f :
                f.write(self.validators_h_create)
            with open('../include/generated/callbacks.def', 'w') as f :
                f.write(self.callbacks_h_create)

def main():
    pcg = PropertyCreateGeneration()
    pcg.run()

if __name__ == "__main__":
    main()
