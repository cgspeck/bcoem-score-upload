from dataclasses import dataclass
from typing import Dict, List, Optional
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from src.models import brewers
from src.models.brewers import Brewer


@dataclass
class Staff:
    id: int
    uid: int
    judge: bool
    steward: bool
    organizer: bool
    staff: bool
    brewer: Optional[Brewer]


@dataclass
class StaffSummary:
    judges: List[Brewer]
    stewards: List[Brewer]
    organizers: List[Brewer]
    staffs: List[Brewer]


def get_staff(cnn: MySQLConnection, with_brewers=True) -> List[Staff]:
    brewers_by_uid: Dict[int, Brewer] = dict()

    if with_brewers:
        brewers_by_uid = brewers.get_brewer_uid_dict(cnn)

    sql = """
SELECT id, uid, staff_judge, staff_steward, staff_organizer, staff_staff
FROM staff
ORDER BY id ASC;
    """
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    memo = []

    for id, uid, judge, steward, organizer, staff in cursor:
        brewer = brewers_by_uid.get(uid, None)

        memo.append(
            Staff(
                id=id,
                uid=uid,
                judge=judge,
                steward=steward,
                organizer=organizer,
                staff=staff,
                brewer=brewer,
            )
        )

    return memo


def get_summary(cnn) -> StaffSummary:
    staff = get_staff(cnn, with_brewers=True)
    judges: List[Brewer] = list()
    stewards: List[Brewer] = list()
    organizers: List[Brewer] = list()
    staffs: List[Brewer] = list()

    for staff_member in staff:
        if staff_member.staff:
            staffs.append(staff_member.brewer)
        if staff_member.judge:
            judges.append(staff_member.brewer)
        if staff_member.organizer:
            organizers.append(staff_member.brewer)
        if staff_member.steward:
            stewards.append(staff_member.brewer)

    judges.sort()
    stewards.sort()
    organizers.sort()
    staffs.sort()

    return StaffSummary(
        judges=judges, stewards=stewards, organizers=organizers, staffs=staffs
    )
