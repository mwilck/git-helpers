# Configuration file git_conf.json

`git_sort` looks for this file in the following locations, with decreasing precedence:

 1. current directory
 2. `$HOME/.config/git_json`
 3. the directory of `git_sort` itself.

# Configuration parameters recognized

## git_dir

Path to the git repository defining the remotes in `head_names`. The
environment variable `GIT_DIR` will override this parameter.
  
## head_names

A list of each remote head which is indexed by this script.
If a commit does not appear in one of these remotes, it is considered "not
upstream" and cannot be sorted.

Each entry has the form [head name, remote branch name, [list of possible remote urls]].
The "head-name" is only used internally by `git_sort`. The name of the remote
in the repository itself may be different, as remotes are matched by URL.

Repositories that come first in the list should be pulling/merging from
repositories lower down in the list. Said differently, commits should trickle
up from repositories at the end of the list to repositories higher up. For
example, network commits usually follow `net-next` -> `net` -> `linux.git`.

