## General Alembic Information
Alembic provides for the creation, management, and invocation of change management scripts for a relational database, using SQLAlchemy as the underlying engine.

For a general tutorial on what each file does within the `migrations` folder, please reference this Alembic tutorial page: [Link](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

## Steps To Create a Data-Migration
1. Make sure `alembic` is installed in your virtual environment.
2. Create a new migration script by entering a command in your terminal similar to this: `alembic revision -m "[THE SLUG FOR YOUR DATA MIGRATION]"`. More details for modifying your migration scripts can be seen here: [Link](https://alembic.sqlalchemy.org/en/latest/tutorial.html#create-a-migration-script).
    - Slugs are kept to a character limit of 40, so please be concise.
3. Once your migration is complete, you will run the command `alembic upgrade head`. For more information on this command, please visit this link: [Link](https://alembic.sqlalchemy.org/en/latest/tutorial.html#create-a-migration-script).
