#!/usr/bin/python

import os, re, time
import hit

class DupWalker(object):
    def __init__(self, fname):
        self.have = {}
        self.dups = {}
        self.errors = []
        self._fname = fname

    def _duperr(self, node):
        if node.type() == hit.NodeType.Section:
            ntype = 'section'
        elif node.type() == hit.NodeType.Field:
            ntype = 'parameter'
        self.errors.append('{}:{}: duplicate {} "{}"'.format(self._fname, node.line(), ntype, node.fullpath()))

    def walk(self, fullpath, path, node):
        if node.type() != hit.NodeType.Field and node.type() != hit.NodeType.Section:
            return

        if fullpath in self.have:
            if fullpath not in self.dups:
                self._duperr(self.have[fullpath])
                self.dups[fullpath] = True
            self._duperr(node)
        else:
            self.have[fullpath] = node


"""
Parser object for reading GetPot formatted files
"""
class Parser:
    def __init__(self, factory, warehouse, check_for_type=True):
        self.factory = factory
        self.warehouse = warehouse
        self.params_parsed = set()
        self.params_ignored = set()
        self._check_for_type = check_for_type

    """
    Parse the passed filename filling the warehouse with populated InputParameter objects
    Error codes:
      0x00 - Success
      0x01 - pyGetpot parsing error
      0x02 - Unrecogonized Boolean key/value pair
      0x04 - Missing required parameter
      0x08 - Bad value
      0x10 - Mismatched type
      0x20 - Missing Node type parameter
      0x40 - Tester creation failed

      If new error codes are added, the static mask value needs to be adjusted
    """
    @staticmethod
    def getErrorCodeMask():
        # See Error codes description above for mask calculation
        return 0x7F

    def parse(self, filename):
        error_code = 0x00

        with open(filename, 'r') as f:
            data = f.read()

        try:
            root = hit.parse(os.path.abspath(filename), data)
        except Exception as err:
            print(err)
            return 0x01 # Parse Error

        w = DupWalker(os.path.abspath(filename))
        root.walk(w, hit.NodeType.All)
        for err in w.errors:
            print err
            error_code = 1

        error_code = self._parseNode(filename, root)
        del root

        if len(self.params_ignored):
            print 'Warning detected when parsing file "' + os.path.join(os.getcwd(), filename) + '"'
            print '       Ignored Parameter(s): ', self.params_ignored

        return error_code

    def extractParams(self, filename, params, getpot_node):
        error_code = 0x00
        full_name = getpot_node.fullpath()

        # Populate all of the parameters of this test node
        # using the GetPotParser.  We'll loop over the parsed node
        # so that we can keep track of ignored parameters as well
        local_parsed = set()
        for child in getpot_node.children(node_type=hit.NodeType.Field):
            key = child.path()
            value = child.raw()

            self.params_parsed.add(child.fullpath())
            local_parsed.add(key)
            if key in params:
                if params.type(key) == list:
                    value = value.replace('\n', ' ')
                    params[key] = re.split('\s+', value)
                else:
                    if re.match('".*"', value):   # Strip quotes
                        params[key] = value[1:-1]
                    else:
                        if key in params.strict_types:
                            # The developer wants to enforce a specific type without setting a valid value
                            strict_type = params.strict_types[key]

                            if strict_type == time.struct_time:
                                # Dates have to be parsed
                                try:
                                    params[key] = time.strptime(value, "%m/%d/%Y")
                                except ValueError:
                                    print "Bad Value for key '" + full_name + '/' + key + "': " + value
                                    params['error_code'] = 0x08
                                    error_code = error_code | params['error_code']
                            elif strict_type != type(value):
                                print "Mismatched type for key '" + full_name + '/' + key + "': " + value
                                params['error_code'] = 0x10
                                error_code = error_code | params['error_code']

                        # Prevent bool types from being stored as strings.  This can lead to the
                        # strange situation where string('False') evaluates to true...
                        elif params.isValid(key) and (type(params[key]) == type(bool())):
                            # We support using the case-insensitive strings {true, false} and the string '0', '1'.
                            if (value.lower()=='true') or (value=='1'):
                                params[key] = True
                            elif (value.lower()=='false') or (value=='0'):
                                params[key] = False
                            else:
                                print "Unrecognized (key,value) pair: (", key, ',', value, ")"
                                params['error_code'] = 0x02
                                error_code = error_code | params['error_code']
                        else:
                            # Otherwise, just do normal assignment
                            params[key] = value
            else:
                self.params_ignored.add(key)

        # Make sure that all required parameters are supplied
        required_params_missing = params.required_keys() - local_parsed
        if len(required_params_missing):
            print 'Error detected when parsing file "' + os.path.join(os.getcwd(), filename) + '"'
            print '       Required Missing Parameter(s): ', required_params_missing
            params['error_code'] = 0x04 # Missing required params
            error_code = params['error_code']

        return error_code

    # private:
    def _parseNode(self, filename, node):
        error_code = 0x00

        if node.find('type'):
            moose_type = node.param('type')

            # Get the valid Params for this type
            params = self.factory.validParams(moose_type)

            # Extract the parameters from the Getpot node
            error_code = error_code | self.extractParams(filename, params, node)

            # Add factory and warehouse as private params of the object
            params.addPrivateParam('_factory', self.factory)
            params.addPrivateParam('_warehouse', self.warehouse)
            params.addPrivateParam('_parser', self)

            # Build the object
            try:
                moose_object = self.factory.create(moose_type, node.path(), params)

                # Put it in the warehouse
                self.warehouse.addObject(moose_object)
            except Exception as e:
                print 'Error creating Tester in "' + os.path.join(os.getcwd(), filename) + '": ', e
                error_code = error_code | 0x40

        # Are we in a tree node that "looks" like it should contain a buildable object?
        elif self._check_for_type and self._looksLikeValidSubBlock(node):
            print 'Error detected when parsing file "' + os.path.join(os.getcwd(), filename) + '"'
            print '       Missing "type" parameter in block'
            error_code = error_code | 0x20

        # Loop over the section names and parse them
        for child in node.children(node_type=hit.NodeType.Section):
            error_code = error_code | self._parseNode(filename, child)

        return error_code

    # This routine returns a Boolean indicating whether a given block
    # looks like a valid subblock. In the Testing system, a valid subblock
    # has a "type" and no children blocks.
    def _looksLikeValidSubBlock(self, node):
        return len(node.children(node_type=hit.NodeType.Field)) \
            and len(node.children(node_type=hit.NodeType.Section)) == 0
