from   base64            import b64encode
from   configparser      import ConfigParser
import logging
import re
from   typing            import Iterable, List, TextIO
from   urllib.parse      import quote
import jinja2
from   nacl              import encoding, public
from   setuptools.config import read_configuration
from   .gh               import GitHub
from   .localrepo        import GHRepo

log = logging.getLogger(__name__)

TRAVIS_BADGE_RGX = re.compile(
    r'^\s*\.\. image::\s*https?://travis-ci\.(?:com|org)/[^/]+/[^/]+\.svg'
)

def template_action(python_versions, extra_testenvs, no_pytest_cov=False):
    jenv = jinja2.Environment(
        loader        = jinja2.PackageLoader("travis2gha", "templates"),
        trim_blocks   = True,
        lstrip_blocks = True,
        autoescape    = False,
    )
    return jenv.get_template("test.yml.j2").render(
        python_versions = python_versions,
        extra_testenvs  = extra_testenvs,
        no_pytest_cov   = no_pytest_cov,
    ).rstrip() + "\n"

def mksecrets(repo: GHRepo, secretsfile: TextIO) -> None:
    cfg = ConfigParser(interpolation=None)
    cfg.read_file(secretsfile)
    try:
        token = cfg["auth"]["token"]
    except KeyError:
        raise RuntimeError("[auth]token not found in secrets file")
    gh = GitHub(token=token)
    secrets = gh.repos[repo.owner][repo.name].actions.secrets
    pubkey = secrets["public-key"].get()  # Has "key" and "key_id" fields
    for name, value in cfg.items("secrets"):
        log.info("Creating secret %r ...", name)
        secrets[name].put(json={
            "encrypted_value": encrypt_secret(pubkey["key"], value),
            "key_id": pubkey["key_id"],
        })

def encrypt_secret(public_key: str, secret_value: str) -> str:
    """ Encrypt a string for use as a GitHub secret using a public key """
    public_key = public.PublicKey(
        public_key.encode("utf-8"),
        encoding.Base64Encoder(),
    )
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")

def update_ci_badge(readme: str, repo: GHRepo, workflow_name: str = "Test") -> str:
    NEW_BADGE = (
        f".. image:: https://github.com/{repo.owner}/{repo.name}/workflows/{quote(workflow_name)}/badge.svg?branch=master\n"
        f"    :target: https://github.com/{repo.owner}/{repo.name}/actions?workflow={quote(workflow_name)}\n"
        "    :alt: CI Status\n"
        "\n"
    )
    paragraphs = list(read_paragraphs(readme.splitlines(keepends=True)))
    for i, para in enumerate(paragraphs):
        if TRAVIS_BADGE_RGX.match(para):
            paragraphs[i] = NEW_BADGE
    return ''.join(paragraphs)

def read_paragraphs(fp: Iterable[str]) -> Iterable[str]:
    # Trailing newlines & blank lines are retained
    para: List[str] = []
    for line in fp:
        if not _is_blank(line) and para and _is_blank(para[-1]):
            yield ''.join(para)
            para = [line]
        else:
            para.append(line)
    if para:
        yield ''.join(para)

def _is_blank(line: str) -> bool:
    return line in ('\n', '\r\n')

def get_python_versions() -> List[str]:
    cfg = read_configuration("setup.cfg")
    python_versions = []
    for clsfr in cfg["metadata"]["classifiers"]:
        if m := re.fullmatch(r'Programming Language :: Python :: (\d+\.\d+)', clsfr):
            python_versions.append(m[1])
    if (
        'Programming Language :: Python :: Implementation :: PyPy'
        in cfg["metadata"]["classifiers"]
    ):
        if any(v.startswith("2.") for v in python_versions):
            python_versions.append("pypy2")
        if any(v.startswith("3.") for v in python_versions):
            python_versions.append("pypy3")
    return python_versions
