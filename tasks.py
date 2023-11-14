"""
tasks.py defines tasks to run via ssh on one of the defined hosts.
The functions with the @task decoration can be executed from the cli
by calling `invoke task arg1 ... argn`, e.g. `invoke backup staging`.
The caller has to be set up to make ssh connections to the intended host
as the defined user.

## Defined tasks
* backup env
    starting a routine to create an encrypted backup of the database
    in the environment `env`.
* deploy env github_user github_token
    downloading the most recent image and code for the given environment,
    then migrating the database if any migrations are necessary,
    finally restarting the docker containers. The GitHub user and token are
    used to download the docker image from the GitHub container registry.
* cleanup env
    do cleanup tasks. At the moment this consists of removing unused docker
    to free up space.
"""
import datetime
import io
import logging
import os
from dataclasses import dataclass
from time import gmtime

from fabric import Connection
from invoke import task


logging.basicConfig(
    format="[{asctime}] {levelname: <8} [{filename}:{lineno}] {message}",
    level=logging.INFO,
    style="{",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logging.Formatter.converter = gmtime


@dataclass
class HostConfig:
    """HostConfig collects parameters for each deployment (prod, staging, etc)"""

    host_name: str
    git_branch: str
    docker_version: str
    github_user: str
    github_token: str
    backup_name: str
    user: str = "deploy-web"
    code_dir: str = "~/OpenOversight"
    backup_dir: str = "~/openoversight_backup/"
    image_path: str = "ghcr.io/lucyparsons/openoversight"
    key_id: str = "OpenOversight"

    def get_connection(self):
        """Return ssh connection as used by fabric for this HostConfig."""
        return Connection(host=self.host_name, user=self.user)


def get_configs(
    env: str = "", github_user: str = "", github_token: str = ""
) -> HostConfig:
    """
    Return a HostConfig based on given environment and GitHub user and token.
    The GitHub user and token can be omitted if no connection to GitHub is needed.
    """
    configs = {
        "staging": HostConfig(
            host_name="staging.openoversight.com",
            git_branch="develop",
            docker_version="latest",
            github_user=github_user,
            github_token=github_token,
            backup_name="backup_staging",
        ),
        "prod": HostConfig(
            host_name="openoversight.com",
            git_branch="main",
            docker_version="stable",
            github_user=github_user,
            github_token=github_token,
            backup_name="backup_prod",
        ),
    }
    return configs[env]


def pull_repository(c: Connection, github_ref: str):
    """Pull the code on the repo down to the server."""
    c.run(f"git fetch origin {github_ref}")
    c.run("git reset --hard FETCH_HEAD")
    c.run("git clean -df")


def migrate(c, config):
    """Run all migrations that have not been applied to the database yet."""
    c.run(
        f"DOCKER_IMAGE_TAG={config.docker_version} docker compose -f docker-compose.prod-img.yml run --rm --no-deps web flask db upgrade",
        echo=True,
    )


def deploy_(c: Connection, config: HostConfig, github_ref: str):
    """Deploy the most recent docker image for the given environment."""
    logging.info("Start new deployment.")
    with c.cd(config.code_dir):
        pwd = io.StringIO(config.github_token)
        logging.info("Get new production docker image.")
        c.run(
            f"docker login ghcr.io -u {config.github_user} --password-stdin",
            in_stream=pwd,
            echo=True,
        )
        c.run(f"docker pull {config.image_path}:{config.docker_version}", echo=True)
        logging.info("Bring down docker containers.")
        c.run(
            f"DOCKER_IMAGE_TAG={config.docker_version} docker compose -f docker-compose.prod-img.yml down",
            echo=True,
        )
        logging.info("Get code changes from repo")
        pull_repository(c, github_ref)
        logging.info("Run necessary migrations.")
        migrate(c, config)
        logging.info("Bring docker service back up.")
        c.run(
            f"DOCKER_IMAGE_TAG={config.docker_version} docker compose -f docker-compose.prod-img.yml up -d",
            echo=True,
        )
        logging.info("Success!")


@task(
    help={
        "environment": "'staging' or 'prod' indicating which environment to target",
        "github_user": "GitHub user name to authenticate with",
        "github_token": "token to use together with github_user",
        "github_ref": "ref of the branch or tag to deploy (e.g. /refs/tag/v1.0.1 or /refs/heads/main)",
    }
)
def deploy(c, environment, github_user, github_token, github_ref):
    """Deploy the most recent docker image for the given environment."""
    config = get_configs(environment, github_user, github_token)
    connection = config.get_connection()
    deploy_(connection, config, github_ref)


def backup_(c: Connection, config: HostConfig):
    """Create a local encrypted backup of the sql database."""
    logging.info("Start creating database backup.")
    with c.cd(config.code_dir):
        c.run(
            f"""echo 'bash -c "pg_dump $SQLALCHEMY_DATABASE_URI -f /backup/backup.sql"' | docker run --env-file=.env --rm -i -v {config.backup_dir}:/backup/ postgres bash"""
        )
    logging.info("gzip backup.")
    backup_path = os.path.join(config.backup_dir, "backup.sql")
    c.run(f"gzip -f {backup_path}")
    backup_timestamped_name = os.path.join(
        config.backup_dir,
        f"{config.backup_name}_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.gz.gpg",
    )
    logging.info("Encrypt backup.")
    c.run(
        f"gpg --output {backup_timestamped_name} --encrypt --trust-model always --batch --no-tty --recipient {config.key_id} {backup_path}.gz"
    )
    c.run(f"rm {backup_path}.gz")
    logging.info("Success!")


@task(
    help={"environment": "'staging' or 'prod' indicating which environment to target"}
)
def backup(c, environment):
    """Create a local encrypted backup of the sql database."""
    config = get_configs(environment)
    connection = config.get_connection()
    backup_(connection, config)


def cleanup_(c: Connection, config: HostConfig):
    """Execute cleanup tasks, usually after deployment"""
    logging.info("Remove unused docker images")
    c.run("docker image prune -f")


@task(
    help={"environment": "'staging' or 'prod' indicating which environment to target"}
)
def cleanup(c, environment):
    """Execute cleanup tasks, usually after deployment."""
    config = get_configs(environment)
    connection = config.get_connection()
    cleanup_(connection, config)
