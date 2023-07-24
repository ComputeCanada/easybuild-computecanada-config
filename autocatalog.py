#!/bin/env python3
import os
import argparse

def create_argparser():
    class HelpFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
        """ Dummy class for RawDescription and ArgumentDefault formatter """

    description = "Automatically catalog large directories for ingestion into CVMFS"
    epilog = ""
    parser = argparse.ArgumentParser(prog="autocatalog",
                                     formatter_class=HelpFormatter,
                                     description=description,
                                     epilog=epilog)

    parser.add_argument("--path", required=True, default=None, help="Root path to automatically catalog")
    parser.add_argument("--size", default=20000, help="Number of items in a folder beyond which a catalog is created")
    parser.add_argument("--dry-run", action='store_true', help="Dry run")

    return parser

def main():
    args = create_argparser().parse_args()

    path = args.path
    size = int(args.size)

    tree = {}
    roots = []
    dirs_in_root = []
    nelems = []
    for root, dirs, files in os.walk(path):
        tree[root] = {'dirs': dirs, 'nelems': len(dirs) + len(files)}

    large_subdirs = extract_large_subdirs(path, tree, size)
    for k, v in large_subdirs.items():
        # create empty ".cvmfscatalog" file in the sub-directory
        catalog_file = os.path.join(k, ".cvmfscatalog")
        if args.dry_run:
            print("[DRY RUN]: Creating %s" % catalog_file)
        else:
            print("Creating %s" % catalog_file)
            with open(catalog_file, 'w') as fp:
                pass


def total_count(path, tree):
    matches = list(filter(lambda x: x.startswith(path), tree.keys()))
    count = sum([tree[x]['nelems'] for x in matches])
    return count


def counts_in_subdirs(path, tree):
    counts = {}
    if path not in tree or 'dirs' not in tree[path]:
        return counts

    for x in tree[path]['dirs']:
        subpath = os.path.join(path, x)
        counts[subpath] = total_count(subpath, tree)
    return counts


def extract_large_subdirs(path, tree, size):
    # add dir to list if its total_count is above size and it contains no directory that is above size
    # else, go down one level
    root_count = total_count(path, tree)
    sub_counts = counts_in_subdirs(path, tree)
    large_subdirs = {k: v for k, v in sub_counts.items() if v > size}
    if root_count > size and not large_subdirs:
        return {path: root_count}
    else:
        results = {}
        for k, v in large_subdirs.items():
            results.update(extract_large_subdirs(k, tree, size))
        return results


if __name__ == "__main__":
    main()
