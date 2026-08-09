# Guide


### How to run migrations

Command	Purpose
- alembic init alembic : 	Initialize Alembic (run once)
- alembic revision --autogenerate -m "msg" :	Create a new migration script based on model changes
- alembic upgrade head :	Apply all pending migrations
- alembic downgrade -1 : Revert the last migration
- alembic history : View the migration history