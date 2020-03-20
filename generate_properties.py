#!/usr/bin/env python3.7

import yaml

class PropertyCreateGeneration :
    def __init__(self) :
        self.code = ""

    def generate_observers(self, obs) :
        l = [ x.strip() for x in obs.split('|')]
        for i in range(0, len(l)) :
            l[i] = 'PDB_' + l[i] + '_PROPERTY'
        return ' | '.join(l) 
    
    def generate_property_create(self, p) :
        self.code += "PROPERTY_CREATE("
        name = list(p.keys())[0]
        nbytes = p[name]['nbytes'] if 'nbytes' in p[name] else '1'
        set = p[name]['set'] if 'set' in p[name] else 'pdb_property_set_private'
        validate = p[name]['validate'] if 'validate' in p[name] else 'NULL'
        get = p[name]['get'] if 'get' in p[name] else 'pdb_property_get_private'
        
        if ('persistent' in p[name]) :
            in_flash = '1' if p[name]['persistent'] == 'true' else '0'
        else :
            in_flash = '0'
            
        if ('observers' in p[name]) :
            observers = self.generate_observers(p[name]['observers'])
        else :
            observers = '0'
            
        out = [name, nbytes, validate, get, set, in_flash, observers, name]
        self.code += ', '.join(out) + ')\n'

    def run(self) :
        with open(r'properties.yaml') as file:
            properties_dict = yaml.load(file, Loader=yaml.FullLoader)
            properties = properties_dict['Properties']
            for p in properties :
                self.generate_property_create(p)
            with open('include/generated/properties.def', 'w') as file_define :
                file_define.write(self.code)

def main():
    pcg = PropertyCreateGeneration()
    pcg.run()
            
if __name__ == "__main__":
    main()
