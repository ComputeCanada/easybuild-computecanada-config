
PREPEND = 1
APPEND = 2
REPLACE = 3

def modify_all_opts(ec, opts_changes):
    if ec['name'] in opts_changes.keys():
        for opt, value in opts_changes[ec['name']]:
            update_opts(ec, value[0], opt, value[1])

def update_opts(ec,changes,key, update_type):
    print("Changing %s from: %s" % (key,ec[key]))
    if isinstance(ec[key], str):
        opts = [ec[key]]
    elif isinstance(ec[key], list):
        opts = ec[key]
    else:
        return
    for i in range(len(opts)):
        if not changes in opts[i]:
            if update_type == PREPEND:
                opts[i] = changes + opts[i]
            elif update_type == APPEND:
                opts[i] = opts[i] + changes
            elif update_type == REPLACE:
                opts[i] = changes

    if isinstance(ec[key], str):
        ec[key] = opts[0]
    print("New %s: %s" % (key,ec[key]))

def package_match(ref, test):
    #print("Testing %s against %s" % (str(test),str(ref)))
    if isinstance(ref,str): ref = (ref, "ANY", "ANY")
    if isinstance(test,list) and isinstance(test[0],tuple): return False  # does not change anything for multi_deps
    ref_name = ref[0]
    ref_version = ref[1]
    ref_version_suffix = "ANY"
    if len(ref) >= 3:
        ref_version_suffix = ref[2]

    test_name = test[0]
    test_version = test[1]
    test_version_suffix = None
    if len(test) >= 3:
        test_version_suffix = test[2]

    # test name
    if ref_name != test_name: return False
    #print("Name matches")

    # test version
    if ref_version != "ANY":
        if isinstance(ref_version, str) and test_version != ref_version:
            return False
        if isinstance(ref_version, tuple) and not test_version in ref_version:
            return False
    #print("Version matches")

    # if we get to this point, the versions match, test version_suffixes
    if ref_version_suffix != "ANY":
        # undefined version_suffix required and version_suffix provided
        if not ref_version_suffix and test_version_suffix:
            return False
        if isinstance(ref_version_suffix, str) and test_version_suffix != ref_version_suffix:
            return False
        if isinstance(ref_version_suffix, tuple) and not test_version_suffix in ref_version_suffix:
            return False
    #print("Version suffix matches")

    return True

def map_dependency_version(dep, new_dep, tc_mapping, mytc):
    if isinstance(dep,tuple): dep = list(dep)
    # ensure that it has a length of 4
    for _ in range(len(dep),4):
        dep.append(None)

    # figure out what is the right toolchain to put there
    new_tc = None
    if 'ALL' in tc_mapping: new_tc = tc_mapping['ALL']
    for tcs in tc_mapping.keys():
        if not isinstance(tcs,tuple): continue
        if mytc == tcs or mytc in tcs:
            new_tc = tc_mapping[tcs]

    if isinstance(new_dep, str): dep[1] = new_dep
    if isinstance(new_dep, tuple):
        dep[1] = new_dep[0]
        dep[2] = new_dep[1]
        if len(new_dep) == 3:
            new_tc = new_dep[2]

    dep[3] = new_tc
    return dep

def replace_dependencies(ec, tc, param, deps_mapping):
    mytc = (ec.toolchain.name, ec.toolchain.version)
    #print("mytc: %s, tc: %s" % (str(mytc), str(tc)))
    if tc == 'ALL' or mytc == tc or mytc in tc:
        #print("toolchain match")
        for n, dep in enumerate(ec[param]):
            dep = list(dep)
            if dep[0] == ec.name:
                print("Dependency has the same name as the easyconfig, not replacing.")
                continue
            for new_dep in deps_mapping['pkg_mapping']:
                new_dep_version = deps_mapping['pkg_mapping'][new_dep]
                if package_match(new_dep, dep):
                    print("Dependency %s matches %s" % (str(dep),(new_dep)))
                    dep = map_dependency_version(dep,new_dep_version,deps_mapping['tc_mapping'],mytc)
                    print("New dependency: %s" % str(dep))
                    dep = tuple(dep)
                    ec[param][n] = dep

def modify_dependencies(ec,param):
    for tc in new_version_mapping:
        deps_mapping = new_version_mapping[tc]
        if tc == 'ALL':
            replace_dependencies(ec,'ALL',param,deps_mapping)
        else:
            replace_dependencies(ec,tc,param,deps_mapping)

    for names in new_version_mapping_app_specific:
        mapping = new_version_mapping_app_specific[names]
        if ec['name'] in names:
            print("Specific dependency mappings exist for %s, applying them" % ec['name'])
            for tc in mapping:
                deps_mapping = mapping[tc]
                replace_dependencies(ec,tc,param,deps_mapping)
