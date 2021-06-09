from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL

import UFCStats.settings

DeclarativeBase = declarative_base()

def db_connect():
    """
    Performs db connection using db settings in settings.py module. Returns sqlalchemy engine instance.
    """
    return create_engine(URL(**UFCStats.settings.DATABASE))


def create_table(engine):
    DeclarativeBase.metadata.create_all(engine)


class EventTable(DeclarativeBase):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    event_id = Column('event_id', String, nullable=True, unique=True)
    event_name = Column('event_name', String, nullable=True)
    event_date =Column('event_date', String, nullable=True) 
    event_city = Column('event_city', String, nullable=True)
    event_country = Column('event_country', String, nullable=True)
    num_fights = Column('num_fights', Integer, nullable=True)
    create_date = Column('create_date', String, nullable=True)

class FightTable(DeclarativeBase):
    __tablename__ = 'fights'
    
    id = Column(Integer, primary_key=True)
    fight_id = Column('fight_id', String, nullable=True, unique=True)
    event_id = Column('event_id', String, nullable=True)
    weightclass = Column('weightclass', String, nullable=True)
    rds_sched = Column('rds_sched', String, nullable=True)
    rd_ended = Column('rd_ended', String, nullable=True)
    method = Column('method', String, nullable=True)
    time_last_rd = Column('time_last_rd', String, nullable=True)
    referee = Column('referee', String, nullable=True)
    bonus = Column('bonus', String, nullable=True)
    fighter_1_id = Column('fighter_1_id', String, nullable=True)
    fighter_2_id = Column('fighter_2_id', String, nullable=True)
    winner_id = Column('winner_id', String, nullable=True)
    taplogy_rank = Column('tapology_rank', Integer, nullable=True)
    judge1 = Column('judge1', String, nullable=True)
    judge2 = Column('judge2', String, nullable=True)
    judge3 = Column('judge3', String, nullable=True)
    judge1_fighter1 = Column('judge1_fighter1', Integer, nullable=True)
    judge1_fighter2 = Column('judge1_fighter2', Integer, nullable=True)
    judge2_fighter1 = Column('judge2_fighter1', Integer, nullable=True)
    judge2_fighter2 = Column('judge2_fighter2', Integer, nullable=True)
    judge3_fighter1 = Column('judge3_fighter1', Integer, nullable=True)
    judge3_fighter2 = Column('judge3_fighter2', Integer, nullable=True)
    media_fighter1 = Column('media_fighter1', Float, nullable=True)
    media_fighter2 = Column('media_fighter2', Float, nullable=True)
    media_count = Column('media_count', Integer, nullable=True)
    deductions = Column('deductions', String, nullable=True)
    create_date = Column('create_date', String, nullable=True)

class RoundTable(DeclarativeBase):
    __tablename__ = 'rounds'
    
    id = Column(Integer, primary_key=True)
    rd_id = Column('rd_id', String, nullable=True, unique=True)
    fight_id = Column('fight_id', String, nullable=True)
    rd_num = Column('rd_num', Integer, nullable=True)
    rd_length = Column('rd_length', Integer, nullable=True)
    judge1_fighter1 = Column('judge1_fighter1', Integer, nullable=True)
    judge1_fighter2 = Column('judge1_fighter2', Integer, nullable=True)
    judge2_fighter1 = Column('judge2_fighter1', Integer, nullable=True)
    judge2_fighter2 = Column('judge2_fighter2', Integer, nullable=True)
    judge3_fighter1 = Column('judge3_fighter1', Integer, nullable=True)
    judge3_fighter2 = Column('judge3_fighter2', Integer, nullable=True)
    create_date = Column('create_date', String, nullable=True)

class RoundResultTable(DeclarativeBase):
    __tablename__ = 'round_results'
    
    # Identifiers
    id = Column(Integer, primary_key=True)
    rd_result_id = Column('rd_result_id', String, nullable=True, unique=True)
    fighter_id = Column('fighter_id', String, nullable=True)
    opponent_id = Column('opponent_id', String, nullable=True)
    rd_id = Column('rd_id', String, nullable=True)
    create_date = Column('create_date', String, nullable=True)
    
    # Offensive
    kd = Column('kd', Integer, nullable=True)
    sig_head_land = Column('sig_head_land', Integer, nullable=True)
    sig_head_att = Column('sig_head_att', Integer, nullable=True)
    sig_body_land = Column('sig_body_land', Integer, nullable=True)
    sig_body_att = Column('sig_body_att', Integer, nullable=True)
    sig_leg_land = Column('sig_leg_land', Integer, nullable=True)
    sig_leg_att = Column('sig_leg_att', Integer, nullable=True)
    sig_dist_land = Column('sig_dist_land', Integer, nullable=True)
    sig_dist_att = Column('sig_dist_att', Integer, nullable=True)
    sig_clinch_land = Column('sig_clinch_land', Integer, nullable=True)
    sig_clinch_att = Column('sig_clinch_att', Integer, nullable=True)
    sig_ground_land = Column('sig_ground_land', Integer, nullable=True)
    sig_ground_att = Column('sig_ground_att', Integer, nullable=True)
    total_strike_land = Column('total_strike_land', Integer, nullable=True)
    total_strike_att = Column('total_strike_att', Integer, nullable=True)
    takedown_land = Column('takedown_land', Integer, nullable=True)
    takedown_att = Column('takedown_att', Integer, nullable=True)
    sub_att = Column('sub_att', Integer, nullable=True)
    reversals = Column('reversals', Integer, nullable=True)
    ctrl_time = Column('ctrl_time', Integer, nullable=True)
    create_date = Column('create_date', String, nullable=True)
    
    # Defensive
    kd_taken = Column('kd_taken', Integer, nullable=True)
    sig_head_taken = Column('sig_head_taken', Integer, nullable=True)
    sig_head_seen = Column('sig_head_seen', Integer, nullable=True)
    sig_body_taken = Column('sig_body_taken', Integer, nullable=True)
    sig_body_seen = Column('sig_body_seen', Integer, nullable=True)
    sig_leg_taken = Column('sig_leg_taken', Integer, nullable=True)
    sig_leg_seen = Column('sig_leg_seen', Integer, nullable=True)
    sig_dist_taken = Column('sig_dist_taken', Integer, nullable=True)
    sig_dist_seen = Column('sig_dist_seen', Integer, nullable=True)
    sig_clinch_taken = Column('sig_clinch_taken', Integer, nullable=True)
    sig_clinch_seen = Column('sig_clinch_seen', Integer, nullable=True)
    sig_ground_taken = Column('sig_ground_taken', Integer, nullable=True)
    sig_ground_seen = Column('sig_ground_seen', Integer, nullable=True)
    total_strike_taken = Column('total_strike_taken', Integer, nullable=True)
    total_strike_seen = Column('total_strike_seen', Integer, nullable=True)
    takedown_taken = Column('takedown_taken', Integer, nullable=True)
    takedown_seen = Column('takedown_seen', Integer, nullable=True)
    sub_seen = Column('sub_seen', Integer, nullable=True)
    reversals_taken = Column('reversals_taken', Integer, nullable=True)
    ctrl_time_taken = Column('ctrl_time_taken', Integer, nullable=True)
    create_date = Column('create_date', String, nullable=True)

class FighterTable(DeclarativeBase):
    __tablename__ = 'fighters'
    
    id = Column(Integer, primary_key=True)
    fighter_id = Column('fighter_id', String, nullable=True, unique=True)
    first_name = Column('first_name', String, nullable=True)
    last_name = Column('last_name', String, nullable=True)
    nickname = Column('nickname', String, nullable=True)
    dob = Column('dob', String, nullable=True)
    gender = Column('gender', String, nullable=True)
    reach = Column('reach', Integer, nullable=True)
    height =Column('height', Integer, nullable=True)
    weight = Column('weight', Integer, nullable=True)
    stance = Column('stance', String, nullable=True)
    wins = Column('wins', Integer, nullable=True)
    losses = Column('losses', Integer, nullable=True)
    draws = Column('draws', Integer, nullable=True)
    belt = Column('belt', String, nullable=True)
    last_fight_date = Column('last_fight_date', String, nullable=True)
    latest_weight_class = Column('latest_weight_class', String, nullable=True)
    create_date = Column('create_date', String, nullable=True)