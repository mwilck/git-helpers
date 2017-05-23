#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import os.path
import pygit2
import shelve
import subprocess
import sys

# a list of each remote head which is indexed by this script
# If a commit does not appear in one of these remotes, it is considered "not
# upstream" and cannot be sorted.
# Repositories that come first in the list should be pulling/merging from
# repositories lower down in the list. Said differently, commits should trickle
# up from repositories at the end of the list to repositories higher up. For
# example, network commits usually follow "net-next" -> "net" -> "linux.git".
# (display name, [list of possible remote urls])
head_names = (
    ("linux.git", [
        "git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git",
        "https://kernel.googlesource.com/pub/scm/linux/kernel/git/torvalds/linux.git",
    ]),
    ("net", [
        "git://git.kernel.org/pub/scm/linux/kernel/git/davem/net.git",
    ]),
    ("net-next", [
        "git://git.kernel.org/pub/scm/linux/kernel/git/davem/net-next.git",
    ]),
)


def _get_heads(repo):
    """
    Returns (display name, sha1)[]
    """
    heads = []
    remotes = {}
    args = ("git", "config", "--get-regexp", "^remote\..+\.url$",)
    for line in subprocess.check_output(args).splitlines():
        name, url = line.split(None, 1)
        name = name.split(".")[1]
        remotes[url] = name

    for display_name, urls in head_names:
        for url in urls:
            if url in remotes:
                try:
                    ref = "%s/master" % (remotes[url],)
                    commit = repo.revparse_single(ref)
                except KeyError:
                    raise Exception("Could not read ref \"%s\", does it not "
                                    "have a master branch?." % (ref,))
                heads.append((display_name, str(commit.id),))
                continue

    # According to the urls in head_names, this is not a clone of linux.git
    # Sort according to commits reachable from the current head
    if not heads or heads[0][0] != head_names[0][0]:
        heads = [("HEAD", str(repo.revparse_single("HEAD").id),)]

    return heads


def _rebuild_history(heads):
    processed = []
    history = {}
    args = ["git", "log", "--topo-order", "--reverse", "--pretty=tformat:%H"]
    for display_name, ref in heads:
        sp = subprocess.Popen(args + processed + [ref], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)

        if display_name in history:
            raise Exception("display name \"%s\" is not unique." %
                            (display_name,))

        history[display_name] = [l.strip() for l in sp.stdout.readlines()]

        sp.communicate()
        if sp.returncode != 0:
            raise Exception("git log exited with an error:\n" + "\n".join(history[display_name]))

        processed.append("^%s" % (ref,))

    return history


def _get_history(heads):
    """
    cache
        heads[]
            (display name, sha1)
        history[display name][]
            git hash represented as string of 40 characters
    """
    cache = shelve.open(os.path.expanduser("~/.cache/git-sort"))
    try:
        c_heads = cache["heads"]
    except KeyError:
        c_heads = None

    if c_heads != heads:
        history = _rebuild_history(heads)
        cache["heads"] = heads
        cache["history"] = history
    else:
        history = cache["history"]
    cache.close()

    return history


def git_sort(repo, mapping):
    heads = _get_heads(repo)
    history = _get_history(heads)
    for display_name, ref in heads:
        for commit in history[display_name]:
            try:
                yield (display_name, mapping.pop(commit),)
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
    num = 0
    for line in sys.stdin.readlines():
        num = num + 1
        try:
            commit = repo.revparse_single(line.strip().split(None, 1)[0])
        except IndexError:
            print("Error: did not find a commit hash on line %d:\n%s" %
                  (num, line.strip(),), file=sys.stderr)
            sys.exit(1)
        h = str(commit.id)
        if h in lines:
            lines[h].append(line)
        else:
            lines[h] = [line]

    for display_name, line_list in git_sort(repo, lines):
        for line in line_list:
            print(line, end="")

    if len(lines) != 0:
        print("Error: the following entries were not found upstream:", file=sys.stderr)
        for line_list in lines.values():
            for line in line_list:
                print(line, end="")
        sys.exit(1)
