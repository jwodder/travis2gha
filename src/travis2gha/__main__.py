import logging
import os.path
from   pathlib    import Path
from   appdirs    import AppDirs
import click
from   .          import core
from   .localrepo import get_local_repo

APPDIRS = AppDirs('travis2gha', 'jwodder')
DEFAULT_SECRETS_FILE = os.path.join(APPDIRS.user_config_dir, "secrets.cfg")

log = logging.getLogger(__name__)

@click.group()
def main():
    """ Switch a repository from Travis to GitHub Actions """
    logging.basicConfig(
        format="[%(levelname)-8s] %(message)s",
        level=logging.INFO,
    )

@main.command()
@click.option(
    '--no-pytest-cov',
    is_flag=True,
    help="Indicates that passing `--cov-report=xml` to the tox run is not an"
         " option and that the XML coverage must be generated externally",
)
@click.option(
    '--testenv',
    nargs=2,
    multiple=True,
    metavar="NAME PYVER",
    help="Configure the generated workflow to also run `tox -e NAME` against"
         " Python version `PYVER`.  Can be specified multiple times.",
)
def run(testenv, no_pytest_cov):
    """
    Create a workflow, update the README badge, populate secrets, and delete
    .travis.yml
    """
    repo = get_local_repo()
    log.info("Detected local GitHub repository: %s", repo.fullname)
    python_versions = core.get_python_versions()
    log.info("Detected supported Python versions: %s", ", ".join(python_versions))
    log.info("Ensuring .github/workflows exists ...")
    wfdir = Path(".github", "workflows")
    wfdir.mkdir(parents=True, exist_ok=True)
    log.info("Creating .github/workflows/test.yml from template ...")
    (wfdir / "test.yml").write_text(
        core.template_action(python_versions, testenv, no_pytest_cov)
    )
    log.info("Updating CI badge in README.rst ...")
    readmepath = Path("README.rst")
    readmepath.write_text(core.update_ci_badge(readmepath.read_text(), repo))
    log.info("Deleting .travis.yml ...")
    Path(".travis.yml").unlink(missing_ok=True)

@main.command()
@click.option(
    '--no-pytest-cov',
    is_flag=True,
    help="Indicates that passing `--cov-report=xml` to the tox run is not an"
         " option and that the XML coverage must be generated externally",
)
@click.option(
    '-o', '--outfile',
    type=click.File("w"),
    default='-',
    help="File to write the workflow to [default: stdout]",
)
@click.option(
    '--testenv',
    nargs=2,
    multiple=True,
    metavar="NAME PYVER",
    help="Configure the generated workflow to also run `tox -e NAME` against"
         " Python version `PYVER`.  Can be specified multiple times.",
)
def workflow(testenv, no_pytest_cov, outfile):
    """ Output a GitHub Actions workflow for the current repository """
    python_versions = core.get_python_versions()
    #log.info("Detected supported Python versions: %s", ", ".join(python_versions))
    print(
        core.template_action(python_versions, testenv, no_pytest_cov),
        end='',
        file=outfile,
    )

@main.command()
@click.option(
    '-S', '--secrets', 'secretsfile',
    type=click.File(),
    default=DEFAULT_SECRETS_FILE,
    help="INI file containing [auth]token and [secrets] sections",
    show_default=True,
)
def secrets(secretsfile):
    """ Create specified workflow secrets in the GitHub repository """
    repo = get_local_repo()
    log.info("Detected local GitHub repository: %s", repo.fullname)
    log.info("Populating secrets ...")
    core.mksecrets(repo, secretsfile)

if __name__ == '__main__':
    main()
