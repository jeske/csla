
# This just returns the full list of paths to append...

def paths(root_dir):
    p = []
    p.append("%s/util" % root_dir)
    p.append("%s/base" % root_dir)
    return p
