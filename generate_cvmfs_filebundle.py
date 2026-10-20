#!/usr/bin/env python3
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys


def get_default_bundle_path(executable_path):
    """
    Returns the default bundle file path: the full path of the completely resolved
    executable target (resolving any symlinks), but with the filename prefixed by .cvmfsbundle-
    as described in https://cvmfs.readthedocs.io/en/2.14/cpt-file-bundles/
    e.g. /cvmfs/example.cern.ch/lib/libexample.so -> /cvmfs/example.cern.ch/lib/.cvmfsbundle-libexample.so
    """
    if not os.path.dirname(executable_path):
        resolved = shutil.which(executable_path)
        full_path = resolved if resolved else executable_path
    else:
        full_path = executable_path

    # Completely resolve symlinks to find the real target executable
    real_path = os.path.realpath(full_path)

    dirname, basename = os.path.split(real_path)
    return os.path.join(dirname, f".cvmfsbundle-{basename}")


def detect_cvmfs_prefix(path):
    """
    Detects the CVMFS repository root prefix from a path if located under /cvmfs.
    e.g. /cvmfs/example.cern.ch/bin/foo -> /cvmfs/example.cern.ch
    """
    norm_path = os.path.realpath(path)
    parts = norm_path.split(os.sep)
    if norm_path.startswith(f"{os.sep}cvmfs{os.sep}"):
        return os.sep.join(parts[:3])
    return ""


def trace_and_generate_cvmfs_bundle(
    executable_path,
    cvmfs_repo_prefix,
    args=None,
    timeout_seconds=60,
    output_file=None,
    follow_forks=False,
):
    """
    Launches an executable, records files opened, resolves relative segments,
    removes the cvmfs_repo_prefix, excludes paths outside of that prefix, and drops directories.
    Writes the resulting bundle specification JSON to output_file (or stdout if output_file is '-').
    """
    if not cvmfs_repo_prefix:
        print("[-] Error: 'cvmfs_repo_prefix' must be defined.", file=sys.stderr)
        return None

    cvmfs_repo_prefix = cvmfs_repo_prefix.rstrip("/")
    repo_prefix_slash = cvmfs_repo_prefix + "/"

    if args is None:
        args = []
    elif isinstance(args, str):
        args = shlex.split(args)
    elif isinstance(args, list) and len(args) == 1 and (" " in args[0] or "\t" in args[0]):
        args = shlex.split(args[0])

    if output_file is None:
        output_file = get_default_bundle_path(executable_path)

    # Build strace command focusing only on open operations
    command = ["strace", "-q"]
    if follow_forks:
        command.append("-f")
    command += ["-e", "trace=open,openat", executable_path] + args

    print(f"[*] Monitoring execution: {' '.join(command)}", file=sys.stderr)
    print(f"[*] Filtering for files under prefix: {cvmfs_repo_prefix}", file=sys.stderr)

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            print(
                f"[-] Execution exceeded {timeout_seconds}s timeout. Capturing partial traces...",
                file=sys.stderr,
            )

    except FileNotFoundError:
        print(
            f"[-] Error: 'strace' or the target executable '{executable_path}' was not found.",
            file=sys.stderr,
        )
        return None

    # Regex to match paths within open/openat calls (accounting for optional [pid ...] prefix from strace -f)
    file_path_regex = re.compile(r'^(?:\[pid\s+\d+\]\s+)?(?:open|openat)\([^,\s]+,\s*"([^"]+)"')
    opened_files = set()

    for line in stderr.splitlines():
        match = file_path_regex.search(line)
        if match:
            raw_path = match.group(1)

            # Resolve relative references like "../" and "./" into a clean canonical path
            normalized_path = os.path.normpath(raw_path)

            # 1. Filter out files outside of the CVMFS repository prefix
            if not normalized_path.startswith(repo_prefix_slash):
                continue

            # 2. Drop the path if it points to a directory instead of a file
            if not os.path.isfile(normalized_path):
                continue

            # Strip the repository prefix out of the path string (relative to repo root)
            rel_path = normalized_path[len(cvmfs_repo_prefix):]
            if not rel_path.startswith("/"):
                rel_path = "/" + rel_path

            opened_files.add(rel_path)

    # Construct the JSON payload strictly following the CernVM-FS specification format
    cvmfs_bundle = {
        "name": "CVMFS_BUNDLE",
        "version": "1.0.0",
        "encoding": "UTF-8",
        "dependencies": sorted(list(opened_files)),
    }

    # Output the formatted JSON structure
    if output_file == "-":
        print(json.dumps(cvmfs_bundle, indent=2))
    else:
        out_dir = os.path.dirname(os.path.abspath(output_file))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(cvmfs_bundle, f, indent=2)
                f.write("\n")
            print(f"[*] Bundle specification written to: {output_file}", file=sys.stderr)
        except OSError as e:
            print(f"[-] Error writing bundle specification to '{output_file}': {e}", file=sys.stderr)
            return None

    return cvmfs_bundle


def main():
    parser = argparse.ArgumentParser(
        description="Run an executable with strace to monitor opened files and generate a CVMFS file bundle specification.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-e", "--executable", "--target-executable",
        dest="executable",
        required=True,
        help="Path to the target executable to run and trace.",
    )
    parser.add_argument(
        "-a", "--args", "--executable-args",
        dest="args",
        nargs="*",
        default=[],
        help="Arguments to forward to the target executable.",
    )
    parser.add_argument(
        "-p", "--cvmfs-prefix", "--prefix",
        dest="cvmfs_prefix",
        default=None,
        help="CVMFS repository prefix to filter and strip (e.g. /cvmfs/example.cern.ch). Auto-detected if executable is under /cvmfs.",
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_file",
        default=None,
        help="Output file path (default: full path of target executable prefixed by '.cvmfsbundle-'; use '-' for stdout).",
    )
    parser.add_argument(
        "-f", "--follow-forks",
        dest="follow_forks",
        action="store_true",
        default=False,
        help="Follow child processes created by fork/clone in strace (passes -f to strace).",
    )
    parser.add_argument(
        "-t", "--timeout",
        dest="timeout",
        type=int,
        default=60,
        help="Execution timeout in seconds.",
    )

    parsed_args = parser.parse_args()

    target_executable = parsed_args.executable
    target_args = parsed_args.args
    cvmfs_prefix = parsed_args.cvmfs_prefix
    output_file = parsed_args.output_file
    timeout = parsed_args.timeout
    follow_forks = parsed_args.follow_forks

    # Auto-detect CVMFS prefix if not provided
    if cvmfs_prefix is None:
        cvmfs_prefix = detect_cvmfs_prefix(target_executable)

    if not cvmfs_prefix:
        parser.error(
            "CVMFS repository prefix could not be determined from the executable path. "
            "Please specify it with -p / --cvmfs-prefix."
        )

    # Determine default output file if not provided
    if output_file is None:
        output_file = get_default_bundle_path(target_executable)

    result = trace_and_generate_cvmfs_bundle(
        executable_path=target_executable,
        cvmfs_repo_prefix=cvmfs_prefix,
        args=target_args,
        timeout_seconds=timeout,
        output_file=output_file,
        follow_forks=follow_forks,
    )
    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
