
PREPEND = 1
APPEND = 2
REPLACE = 3
APPEND_LIST = 4

def modify_all_opts(ec, opts_changes):
    if 'modaltsoftname' in ec and ec['modaltsoftname'] in opts_changes:
        name = ec['modaltsoftname']
    else:
        name = ec['name']

    if name in opts_changes.keys():
        for opt, value in opts_changes[name].items():
            # we don't modify those in this stage
            if opt in ['builddependencies', 'dependencies', 'modluafooter', 'toolchainopts']:
                continue
            update_opts(ec, value[0], opt, value[1])

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

        if isinstance(ec[key], str):
            ec[key] = opts[0]

    print("New %s: %s" % (key,ec[key]))

