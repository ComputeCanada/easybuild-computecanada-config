
PREPEND = 1
APPEND = 2
REPLACE = 3
APPEND_LIST = 4
DROP = 5

def modify_all_opts(ec, opts_changes,
        opts_to_skip=['builddependencies', 'dependencies', 'modluafooter', 'toolchainopts', 'version'],
        opts_to_change='ALL'):
    if 'modaltsoftname' in ec and ec['modaltsoftname'] in opts_changes:
        name = ec['modaltsoftname']
    else:
        name = ec['name']

    possible_keys = [(name, ec['version']), name]

    for key in possible_keys:
        if key in opts_changes.keys():
            for opt, value in opts_changes[key].items():
                # we don't modify those in this stage
                if opt in opts_to_skip:
                    continue
                if opts_to_change == 'ALL' or opt in opts_to_change:
                    update_opts(ec, value[0], opt, value[1])
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

