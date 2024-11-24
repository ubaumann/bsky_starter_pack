import logging
from typing import Annotated, Dict, List

import typer
from ruamel.yaml import YAML
from pydantic import BaseModel, RootModel

from atproto_client import Client, models
from atproto_identity.resolver import IdResolver


logger = logging.getLogger(__name__)


class BskyUser(RootModel):
    """Model for a user in the users.yaml file."""

    root: str


class UserModel(BaseModel):
    """Model for the users.yaml file."""

    starterpacks: Dict[str, List[BskyUser]]


def load_users(user_file: str) -> UserModel:
    """Load users from a YAML file and validate the data."""
    yaml = YAML(typ="safe")
    with open(user_file) as fp:
        data = yaml.load(fp)
    return UserModel.model_validate(data)


def update_starterpack(
    username: Annotated[str, typer.Option(envvar="BSKY_USERNAME")] = "bsky@m.ubaumann.ch",
    password: str = typer.Option(prompt=True, hide_input=True, envvar="BSKY_PASSWORD"),
) -> None:
    """Update the starter packs in the Bsky platform."""
    client = Client()
    client.login(username, password)
    me = client.me

    starter_packs = client.app.bsky.graph.starterpack.list(me.did)
    existing_service_packs = {item.name: item.list for item in starter_packs.records.values()}

    for sp_name, user_list in load_users("bsky_users.yaml").starterpacks.items():
        list_uri = existing_service_packs[sp_name]

        sp_list = client.app.bsky.graph.get_list(models.AppBskyGraphGetList.Params(list=list_uri))
        sp_list_users = [item.subject.handle for item in sp_list.items]

        for new_user in user_list:
            if new_user.root in sp_list_users:
                logger.debug("User %s exists in %s", new_user.root, sp_name)
                continue
            new_user_did = IdResolver().handle.resolve(new_user.root)

            r = client.app.bsky.graph.listitem.create(
                me.did,
                models.AppBskyGraphListitem.Record(
                    list=list_uri,
                    subject=new_user_did,
                    created_at=client.get_current_time_iso(),
                ),
            )
            logger.debug(r)
            logger.info("User %s added to starter pack %s", new_user.root, sp_name)


if __name__ == "__main__":
    logging.basicConfig(filename="logs.log", level=logging.INFO)
    typer.run(update_starterpack)
