import collections
PREPEND = 1
APPEND = 2
REPLACE = 3
APPEND_LIST = 4
DROP = 5
PREPEND_LIST = 6
DROP_FROM_LIST = 7
REPLACE_IN_LIST = 8

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
        try_keys = [(name, version, versionsuffix), (name, version), (name, 'ANY', versionsuffix), name ]
    else:
        try_keys = [(name, 'ANY', versionsuffix), name]
    matching_keys = [key for key in try_keys if key in dictionary]

    return matching_keys

def modify_all_opts(ec, opts_changes, opts_to_skip=None, opts_to_change='ALL'):
    matching_keys = get_matching_keys_from_ec(ec, opts_changes)

    if opts_to_skip is None:
        opts_to_skip = []
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
    orig = ec.get(key)
    if update_type == REPLACE:
        ec[key] = changes
    elif update_type in [APPEND_LIST, PREPEND_LIST, DROP_FROM_LIST, REPLACE_IN_LIST]:
        if not isinstance(changes,list):
            changes = [changes]
        for change in changes:
            if update_type == APPEND_LIST:
                ec[key].append(change)
            elif update_type == DROP_FROM_LIST:
                ec[key] = [x for x in ec[key] if x not in changes]
            elif update_type == REPLACE_IN_LIST:
                for swap in changes:
                    ec[key] = [swap[1] if x == swap[0] else x for x in ec[key]]
            else:
                ec[key].insert(0, change)
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

    if str(ec[key]) != str(orig):
        print("%s: Changing %s from: %s to: %s" % (ec.filename(),key,orig,ec[key]))

