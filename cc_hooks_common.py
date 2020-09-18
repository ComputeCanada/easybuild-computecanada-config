import collections
PREPEND = 1
APPEND = 2
REPLACE = 3
APPEND_LIST = 4
DROP = 5

def get_matching_keys_from_ec(ec, dictionary):
    if 'modaltsoftname' in ec:
        matching_keys = get_matching_keys(ec['modaltsoftname'], ec['version'], ec['versionsuffix'], dictionary)
    if not matching_keys:
        matching_keys = get_matching_keys(ec['name'], ec['version'], ec['versionsuffix'], dictionary)
    return matching_keys

def get_matching_keys(name, version, versionsuffix, dictionary):
    matching_keys = []
    #version can sometimes be a dictionary, which is not hashable
    if isinstance(version, collections.Hashable):
        try_keys = [name, (name, version), (name, version, versionsuffix), (name, 'ANY', versionsuffix)]
    else:
        try_keys = [name, (name, 'ANY', versionsuffix)]
    matching_keys = [key for key in try_keys if key in dictionary]

    return matching_keys

def modify_all_opts(ec, opts_changes,
        opts_to_skip=['builddependencies', 'dependencies', 'modluafooter', 'toolchainopts', 'version', 'multi_deps'],
        opts_to_change='ALL'):
    matching_keys = get_matching_keys_from_ec(ec, opts_changes)

    for key in matching_keys:
        if key in opts_changes.keys():
            for opt, value in opts_changes[key].items():
                # we don't modify those in this stage
                if opt in opts_to_skip:
                    continue
                if opts_to_change == 'ALL' or opt in opts_to_change:
                    if isinstance(value, list):
                        values = value
                    else:
                        values = [value]

                    for v in values:
                        update_opts(ec, v[0], opt, v[1])
            break

def update_opts(ec,changes,key, update_type):
    print("Changing %s from: %s" % (key,ec[key]))
    if update_type == REPLACE:
        ec[key] = changes
    elif update_type == APPEND_LIST:
        if not isinstance(changes,list):
            changes = [changes]
        for change in changes:
            ec[key].append(change)
    else:
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
            elif update_type == DROP:
                opts[i] = opts[i].replace(changes,'')

        if isinstance(ec[key], str):
            ec[key] = opts[0]

    print("New %s: %s" % (key,ec[key]))

