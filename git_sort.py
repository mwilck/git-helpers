#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import os.path
import pygit2
import shelve
import subprocess
import sys


def _get_heads(repo):
    heads = {}
    head_names = [
        "origin/master",
        "net/master",
        "net-next/master",
    ]

    for name in head_names:
        try:
            commit = repo.revparse_single(name)
        except KeyError:
            pass
        else:
            heads[name] = str(commit.id)
    if len(heads) == 0:
        raise Exception("Couldn't find any heads, edit the \"head_names\" variable.")

    return heads


def _get_history(heads):
    """
    cache
        heads[name]
            ref
        history[]
            git hash as 40 hex char string
    """
    cache = shelve.open(os.path.expanduser("~/.cache/git-sort"))
    try:
        c_heads = cache["heads"]
    except KeyError:
        c_heads = None

    if c_heads != heads:
        args = ["git", "log", "--topo-order", "--reverse", "--pretty=tformat:%H"]
        args.extend(heads.keys())
        sp = subprocess.Popen(args, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)

        history = [l.strip() for l in sp.stdout.readlines()]

        sp.communicate()
        if sp.returncode != 0:
            print("\n".join(history), file=sys.stderr)
            raise Exception("git log exited with an error")
        cache["heads"] = heads
        cache["history"] = history
    else:
        history = cache["history"]
    cache.close()

    return history


def git_sort(repo, mapping):
    heads = _get_heads(repo)
    history = _get_history(heads)
    for commit in history:
        try:
            yield mapping.pop(commit)
        except KeyError:
            pass

    return


if __name__ == "__main__":
    try:
        path = os.environ["GIT_DIR"]
    except KeyError:
        path = pygit2.discover_repository(os.getcwd())
    repo = pygit2.Repository(path)

    lines = {}
    for line in sys.stdin.readlines():
        commit = repo.revparse_single(line.strip().split(None, 1)[0])
        h = str(commit.id)
        if h in lines:
            lines[h].append(line)
        else:
            lines[h] = [line]

    for line_list in git_sort(repo, lines):
        for line in line_list:
            print(line, end="")

    if len(lines) != 0:
        print("Error: the following entries were not found upstream:", file=sys.stderr)
        for line_list in lines.values():
            for line in line_list:
                print(line, end="")
        sys.exit(1)
