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
    Returns the default bundle file path: the full path of the executable being run,
    but with the executable filename prefixed by .cvmfsbundle-
    as described in https://cvmfs.readthedocs.io/en/2.14/cpt-file-bundles/
    e.g. /cvmfs/example.cern.ch/lib/libexample.so -> /cvmfs/example.cern.ch/lib/.cvmfsbundle-libexample.so
    """
    if not os.path.dirname(executable_path):
        resolved = shutil.which(executable_path)
        full_path = os.path.abspath(resolved) if resolved else os.path.abspath(executable_path)
    else:
        full_path = os.path.abspath(executable_path)

    dirname, basename = os.path.split(full_path)
    return os.path.join(dirname, f".cvmfsbundle-{basename}")


def detect_cvmfs_prefix(path):
    """
    Detects the CVMFS repository root prefix from a path if located under /cvmfs.
    e.g. /cvmfs/example.cern.ch/bin/foo -> /cvmfs/example.cern.ch
    """
    norm_path = os.path.abspath(path)
    parts = norm_path.split(os.sep)
    if len(parts) >= 3 and parts[1] == "cvmfs" and parts[2]:
        return f"/cvmfs/{parts[2]}"
    return ""


def trace_and_generate_cvmfs_bundle(
    executable_path,
    args=None,
    timeout_seconds=60,
    cvmfs_repo_prefix="",
    output_file=None,
):
    """
    Launches an executable, records files opened, resolves relative segments,
    removes the cvmfs_prefix, excludes paths outside of that prefix, and drops directories.
    Writes the resulting bundle specification JSON to output_file (or stdout if output_file is '-').
    """
    if args is None:
        args = []
    elif isinstance(args, str):
        args = shlex.split(args)
    elif isinstance(args, list) and len(args) == 1 and (" " in args[0] or "\t" in args[0]):
        args = shlex.split(args[0])

    if output_file is None:
        output_file = get_default_bundle_path(executable_path)

    # Build strace command focusing only on open operations
    command = ["strace", "-q", "-e", "trace=open,openat", executable_path] + args

    print(f"[*] Monitoring execution: {' '.join(command)}", file=sys.stderr)
    if cvmfs_repo_prefix:
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

    # Regex to match paths within open/openat calls
    file_path_regex = re.compile(r'^(?:open|openat)\([^,\s]+,\s*"([^"]+)"')
    opened_files = set()

    # System path prefixes to ignore for CVMFS dependencies
    ignored_prefixes = ("/proc/", "/dev/", "/sys/", "/etc/")

    for line in stderr.splitlines():
        match = file_path_regex.search(line)
        if match:
            raw_path = match.group(1)

            # Resolve relative references like "../" and "./" into a clean canonical path
            normalized_path = os.path.normpath(raw_path)

            # 1. Filter out standard Linux virtual file systems / transient configurations
            if normalized_path.startswith(ignored_prefixes):
                continue

            # 2. Drop the path if it points to a directory instead of a file
            if not os.path.isfile(normalized_path):
                continue

            # 3. Handle repository prefix filtering
            if cvmfs_repo_prefix:
                prefix = cvmfs_repo_prefix.rstrip("/")
                # Drop any file path that does NOT start with the repository directory
                if not (normalized_path == prefix or normalized_path.startswith(prefix + "/")):
                    continue

                # Strip the prefix out of the path string
                normalized_path = normalized_path[len(prefix):]

            # Ensure path starts with an absolute slash relative to the repo root
            if not normalized_path.startswith("/"):
                normalized_path = "/" + normalized_path

            opened_files.add(normalized_path)

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

    # Auto-detect CVMFS prefix if not provided
    if cvmfs_prefix is None:
        cvmfs_prefix = detect_cvmfs_prefix(target_executable)

    # Determine default output file if not provided
    if output_file is None:
        output_file = get_default_bundle_path(target_executable)

    result = trace_and_generate_cvmfs_bundle(
        executable_path=target_executable,
        args=target_args,
        timeout_seconds=timeout,
        cvmfs_repo_prefix=cvmfs_prefix,
        output_file=output_file,
    )
    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
