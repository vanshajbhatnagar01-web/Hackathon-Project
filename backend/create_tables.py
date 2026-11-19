
from app.database import engine, Base
from app import models

# Create all tables defined in models.py
Base.metadata.create_all(bind=engine)

print("Growth360 database tables created successfully!")

# Display the table names
for table_name in Base.metadata.tables:
    print("-", table_name)
