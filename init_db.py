from crm.database import Base, engine
from crm import models


Base.metadata.create_all(bind=engine)

print("Tables créées")
