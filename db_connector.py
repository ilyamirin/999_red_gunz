import logging

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(levelname)s : %(asctime)s : %(name)s : %(message)s')
stream_formatter = logging.Formatter('%(levelname)s : %(name)s : %(message)s')

file_handler = logging.FileHandler('logs/db_logs.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(stream_formatter)
stream_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# SQL CONNECTING

with open('db_config.txt', 'r') as config:
    db_username = config.readline().strip()
    db_password = config.readline().strip()
    db_host = config.readline().strip()
    db_name = config.readline().strip()

engine = create_engine(f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}/{db_name}", echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


# DEFINING TABLES

class Users(Base):
    __tablename__ = 'Users'

    user_id = Column(String, primary_key=True)
    first_name = Column(String, nullable=False)
    chat_id = Column(String, nullable=False)
    region = Column(String, nullable=True)


class Bills(Base):
    __tablename__ = 'Bills'

    bill_id = Column(String, primary_key=True)
    title = Column(String)
    date = Column(Date, nullable=False)
    is_note = Column(Boolean, nullable=False)
    is_pdf = Column(Boolean, nullable=False)
    is_secret = Column(Boolean, nullable=False)
    vote_for = Column(Integer, nullable=False)
    vote_against = Column(Integer, nullable=False)
    not_voted = Column(Integer, nullable=False)
    abstained = Column(Integer, nullable=False)


class Answers(Base):
    __tablename__ = 'Answers'

    user_id = Column(String, primary_key=True)
    bill_id = Column(String, primary_key=True)
    user_vote = Column(Integer, nullable=False)


# CREATE TABLES IF THERE'S NONE
result = Base.metadata.create_all(engine)


# Drop table by name
def drop_table(name, base=Base):
    try:
        table = base.metadata.tables[name]
        table.drop(engine)
        logger.info(f"Table {name} deleted!")
        return True
    except KeyError:
        logger.warning(f"Trying to delete table - {name} that doesn't exist.")
        return False


# Functions for adding new data
def add_user(user_data):
    try:
        session = Session()
        new_user = Users(
            user_id=user_data['user_id'],
            first_name=user_data['first_name'],
            chat_id=user_data['chat_id'],
            region=user_data['region'],
        )
        session.add(new_user)
        session.commit()
        logger.info(f"New user {user_data['user_id']} added.")
        return True
    except Exception as e:
        logger.warning(f"New user {user_data['user_id']} was not added.")
        logger.exception(e)
        return False


def add_bill(bill_data):
    try:
        session = Session()
        new_bill = Bills(
            bill_id=bill_data['bill_id'],
            title=bill_data['title'],
            date=bill_data['date'],
            is_note=bill_data['is_note'],
            is_pdf=bill_data['is_pdf'],
            is_secret=bill_data['is_secret'],
            vote_for=bill_data['vote_for'],
            vote_against=bill_data['vote_against'],
            not_voted=bill_data['not_voted'],
            abstained=bill_data['abstained'],
        )
        session.add(new_bill)
        session.commit()
        logger.info(f"New bill {bill_data['bill_id']} added.")
        return True
    except Exception as e:
        logger.warning(f"New bill {bill_data['bill_id']} was not added.")
        logger.exception(e)
        return False


def add_answer(answer_data):
    try:
        session = Session()
        new_answer = Answers(
            user_id=answer_data['user_id'],
            bill_id=answer_data['bill_id'],
            user_vote=answer_data['user_vote'],
        )
        session.add(new_answer)
        session.commit()
        logger.info(f"User {answer_data['user_id']} just added new answer.")
        return True
    except Exception as e:
        logger.warning(f"User {answer_data['user_id']} couldn't add an answer.")
        logger.exception(e)
        return False


# functions for updating data

def user_region_update(user_id,region):
    try:
        session = Session()
        user = session.query(Users).filter_by(user_id=str(user_id)).one()
        user.region = region
        session.commit()
        logger.info(f"user {user_id} region updated {region}")
        return True
    except Exception as e:
        logger.exception(e)
        logger.warning('Region was not added!')
        return False


# GET BILL BY ID

def get_bill_by_id(user_id,bill_id):
    session = Session()
    old_bill_ids = session.query(Answers.bill_id).filter_by(user_id=str(user_id)).all()
    if not old_bill_ids:
        old_bill_ids = []
    bill = session.query(Bills).filter_by(bill_id=bill_id).filter(Bills.bill_id.notin_(old_bill_ids)).first()
    if bill:
        return bill
    else:
        return None


# GET NEW BILL BY USER ID

def get_new_bill_by_id(user_id):
    session = Session()
    old_bill_ids = session.query(Answers.bill_id).filter_by(user_id=str(user_id)).all()
    #bill = session.query(Bills).filter(Bills.bill_id.notin_(old_bill_ids)).order_by(Bills.date.desc()).first()
    bill = session.query(Bills).order_by(Bills.date.desc()).first()
    if bill:
        return bill
    else:
        return None


# CHECK IF BILL WITH THAT ID EXISTS

def check_bill(bill_id):
    session = Session()
    bill = session.query(Bills.bill_id).filter_by(bill_id=str(bill_id)).first()
    if bill:
        return True
    else:
        return False


# CHECK IF USER EXISTS

def check_user(user_id):
    session = Session()
    user = session.query(Users.user_id).filter_by(user_id=str(user_id)).first()
    if user:
        return True
    else:
        return False


def get_user_region(user_id):
    try:
        session = Session()
        region = session.query(Users.region).filter_by(user_id=str(user_id)).one()[0]
        return region
    except Exception as e:
        logger.exception(e)
        return None


# GET PATH FOR FILES
def get_files_paths(bill_id):
    session = Session()
    bill = session.query(Bills).filter_by(bill_id=bill_id).one()
    pdf_path = None
    note_path = None
    if bill.is_note:
        note_path = f'notes/{bill_id}.docx'
    if bill.is_pdf:
        pdf_path = f'pdf_docs/{bill_id}.pdf'
    return pdf_path, note_path


def delete_bill_by_id(bill_id):
    try:
        session = Session()
        bill = session.query(Bills).filter_by(bill_id=bill_id).one()
        session.delete(bill)
        session.commit()
        return True
    except Exception as e:
        logger.exception(e)
        return False


def drop_all():
   drop_table('Users')
    drop_table('Bills')
    drop_table('Answers')
    return True

