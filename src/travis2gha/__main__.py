import os.path
from   pathlib    import Path
from   appdirs    import AppDirs
import click
from   .          import core
from   .localrepo import get_local_repo

APPDIRS = AppDirs('travis2gha', 'jwodder')
DEFAULT_SECRETS_FILE = os.path.join(APPDIRS.user_config_dir, "secrets.cfg")

@click.group()
def main():
    pass

@main.command()
@click.option(
    '-S', '--secrets', 'secretsfile',
    type=click.File(),
    default=DEFAULT_SECRETS_FILE,
    help="INI file containing [auth]token and [secrets] sections",
    show_default=True,
)
@click.option('--testenv', nargs=2, multiple=True)
def run(secretsfile, testenv):
    repo = get_local_repo()
    python_versions = core.get_python_versions()
    wfdir = Path(".github", "workflows")
    wfdir.mkdir(parents=True, exist_ok=True)
    (wfdir / "test.yml").write_text(core.template_action(python_versions, testenv))
    readmepath = Path("README.rst")
    readmepath.write_text(core.update_ci_badge(readmepath.read_text(), repo))
    core.mksecrets(repo, secretsfile)
    Path(".travis.yml").unlink(missing_ok=True)

@main.command()
@click.option('-o', '--outfile', type=click.File("w"), default='-')
@click.option('--testenv', nargs=2, multiple=True)
def template(testenv, outfile):
    python_versions = core.get_python_versions()
    print(core.template_action(python_versions, testenv), end='', file=outfile)

@main.command()
@click.option(
    '-S', '--secrets', 'secretsfile',
    type=click.File(),
    default=DEFAULT_SECRETS_FILE,
    help="INI file containing [auth]token and [secrets] sections",
    show_default=True,
)
def secrets(secretsfile):
    core.mksecrets(get_local_repo(), secretsfile)

if __name__ == '__main__':
    main()
