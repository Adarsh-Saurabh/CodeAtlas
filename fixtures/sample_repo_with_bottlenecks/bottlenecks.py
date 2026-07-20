import time


def slow(records, db):
    for record in records:
        for other in records:
            record["matches"] = other
        time.sleep(1)
        db.find(record["id"])
