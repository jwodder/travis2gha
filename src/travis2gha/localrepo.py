from   dataclasses import dataclass
from   os          import PathLike
import re
import subprocess
from   typing      import Optional, Union

AnyPath = Union[str, bytes, PathLike[str], PathLike[bytes]]

GITHUB_REMOTE_RGX = re.compile(r'''
    (?:
        (?:https?://)?(?:www\.)?github\.com/
        |git(?:://github\.com/|@github\.com:)
    )
    (?P<fullname>
        (?P<owner>(?![Nn][Oo][Nn][Ee]($|[^-A-Za-z0-9]))[-_A-Za-z0-9]+)
        /(?P<name>
            (?:\.?[-A-Za-z0-9_][-A-Za-z0-9_.]* | \.\.[-A-Za-z0-9_.]+)(?<!\.git)
        )
    )
    (?:\.git)?/?
''', flags=re.X)

@dataclass
class GHRepo:
    owner: str
    name: str

    @property
    def fullname(self) -> str:
        return f"{self.owner}/{self.name}"


def parse_github_remote(url: str) -> GHRepo:
    if m := GITHUB_REMOTE_RGX.fullmatch(url):
        return GHRepo(owner=m["owner"], name=m["name"])
    else:
        raise ValueError(f"Invalid GitHub remote URL: {url!r}")

def get_local_repo(chdir: Optional[AnyPath] = None, remote: str = "origin") -> GHRepo:
    r = subprocess.run(
        ["git", "remote", "get-url", remote],
        cwd=chdir,
        capture_output=True,
        text=True,
    )
    if r.returncode == 0:
        url = r.stdout.strip()
        return parse_github_remote(url)
    else:
        raise RuntimeError(
            f"'git remote get-url {remote}' exited with {r.returncode}:\n"
            f"{r.stderr}"
        )
