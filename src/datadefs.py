from dataclasses import asdict, dataclass
from typing import Union


PHPKEY_DBCONFIG_MAP = {
    "$username": "user",
    "$password": "password",
    "$hostname": "host",
    "$database": "database",
    "$database_port": "port",
}


@dataclass
class DBConfig:
    user: str
    password: str
    host: str
    database: str
    port: int

    def to_dict(self) -> dict[str, Union[str, int]]:
        return asdict(self)
