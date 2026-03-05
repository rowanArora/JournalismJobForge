from sqlmodel import create_engine, Session

from backend.config import MODE

DATABASE_URL = "postgresql+psycopg2://aryamanarora@localhost:5432/journalism_job_forge"
ECHO = True if MODE == "debug" else False

engine = create_engine(DATABASE_URL, echo=ECHO)

def get_session():
    with Session(engine) as session:
        yield session
