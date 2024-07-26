from dataclasses import dataclass
from typing import List
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor


@dataclass
class Sponsor:
    id: int
    name: str
    image: str
    image_href: str
    text: str
    location: str
    level: int

    def __lt__(s, o):
        if not isinstance(o, s.__class__):
            return False

        return s.level < o.level

    def __gt__(s, o):
        return not s < o


def get_sponsors(
    cnn: MySQLConnection,
    image_url_prefix="https://comps.westgatebrewers.org/user_images/",
) -> List[Sponsor]:
    sql = """
SELECT id, sponsorName, sponsorImage, sponsorText, sponsorLocation, sponsorLevel, sponsorEnable
FROM sponsors
WHERE sponsorEnable = "1"
ORDER BY sponsorLevel ASC, sponsorName ASC;
    """
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    memo = []

    for id, name, image, text, location, level, _enable in cursor:
        memo.append(
            Sponsor(
                id=id,
                name=name,
                image=image,
                text=text,
                location=location,
                level=int(level),
                image_href=f"{image_url_prefix}{image}",
            )
        )

    memo.sort()

    return memo
