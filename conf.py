from prisma import Prisma

db = Prisma()
if not db.is_connected():
    db.connect()
