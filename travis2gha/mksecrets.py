#!/usr/bin/env python3
from   base64     import b64encode
import json
from   subprocess import CalledProcessError, check_output
import sys
import click
from   nacl       import encoding, public
from   .gh        import GitHub

@click.command()
@click.argument("repository")  # in owner/name format
@click.argument("secretsfile", type=click.File())
def main(repository, secretsfile):
    with secretsfile:
        secrets = json.load(secretsfile)
    token = cmdline("git", "config", "hub.oauthtoken")
    gh = GitHub(token=token)
    secretEP = gh.repos[repository].actions.secrets
    pubkey = secretEP["public-key"].get()  # Has "key" and "key_id" fields
    for name, value in secrets.items():
        secretEP[name].put(json={
            "encrypted_value": encrypt(pubkey["key"], value),
            "key_id": pubkey["key_id"],
        })

def encrypt(public_key: str, secret_value: str) -> str:
    """ Encrypt a Unicode string using the public key. """
    public_key = public.PublicKey(
        public_key.encode("utf-8"),
        encoding.Base64Encoder(),
    )
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")

def cmdline(*args, **kwargs):
    try:
        return check_output(args, universal_newlines=True, **kwargs).strip()
    except CalledProcessError as e:
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
