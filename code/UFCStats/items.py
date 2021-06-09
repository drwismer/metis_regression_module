# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field
from scrapy.loader.processors import TakeFirst


class Event(Item):
    event_id = Field(output_processor=TakeFirst())
    event_name = Field(output_processor=TakeFirst())
    event_date = Field(output_processor=TakeFirst())
    event_city = Field(output_processor=TakeFirst())
    event_country = Field(output_processor=TakeFirst())
    event_type = Field(output_processor=TakeFirst())
    num_fights = Field(output_processor=TakeFirst())
    create_date = Field(output_processor=TakeFirst())

class Fight(Item):
    fight_id = Field(output_processor=TakeFirst())
    event_id = Field(output_processor=TakeFirst())
    weightclass = Field(output_processor=TakeFirst())
    rds_sched = Field(output_processor=TakeFirst())
    method = Field(output_processor=TakeFirst())
    rd_ended = Field(output_processor=TakeFirst())
    time_last_rd = Field(output_processor=TakeFirst())
    referee = Field(output_processor=TakeFirst())
    bonus = Field(output_processor=TakeFirst())
    fighter_1_id = Field(output_processor=TakeFirst())
    fighter_2_id = Field(output_processor=TakeFirst())
    winner_id = Field(output_processor=TakeFirst())
    tapology_rank = Field(output_processor=TakeFirst())
    create_date = Field(output_processor=TakeFirst())

class Round(Item):
    rd_id = Field(output_processor=TakeFirst())
    fight_id = Field(output_processor=TakeFirst())
    rd_num = Field(output_processor=TakeFirst())
    rd_length = Field(output_processor=TakeFirst())
    create_date = Field(output_processor=TakeFirst())

class RoundResult(Item):
    # Identifiers
    rd_result_id = Field(output_processor=TakeFirst())
    fight_id = Field(output_processor=TakeFirst())
    fighter_id = Field(output_processor=TakeFirst())
    opponent_id = Field(output_processor=TakeFirst())
    rd_id = Field(output_processor=TakeFirst())
    create_date = Field(output_processor=TakeFirst())
    
    # Offensive
    kd = Field(output_processor=TakeFirst())
    sig_head_land = Field(output_processor=TakeFirst())
    sig_head_att = Field(output_processor=TakeFirst())
    sig_body_land = Field(output_processor=TakeFirst())
    sig_body_att = Field(output_processor=TakeFirst())
    sig_leg_land = Field(output_processor=TakeFirst())
    sig_leg_att = Field(output_processor=TakeFirst())
    sig_dist_land = Field(output_processor=TakeFirst())
    sig_dist_att = Field(output_processor=TakeFirst())
    sig_clinch_land = Field(output_processor=TakeFirst())
    sig_clinch_att = Field(output_processor=TakeFirst())
    sig_ground_land = Field(output_processor=TakeFirst())
    sig_ground_att = Field(output_processor=TakeFirst())
    total_strike_land = Field(output_processor=TakeFirst())
    total_strike_att = Field(output_processor=TakeFirst())
    takedown_land = Field(output_processor=TakeFirst())
    takedown_att = Field(output_processor=TakeFirst())
    sub_att = Field(output_processor=TakeFirst())
    reversals = Field(output_processor=TakeFirst())
    ctrl_time = Field(output_processor=TakeFirst())
    
    # Defensive
    kd_taken = Field(output_processor=TakeFirst())
    sig_head_taken = Field(output_processor=TakeFirst())
    sig_head_seen = Field(output_processor=TakeFirst())
    sig_body_taken = Field(output_processor=TakeFirst())
    sig_body_seen = Field(output_processor=TakeFirst())
    sig_leg_taken = Field(output_processor=TakeFirst())
    sig_leg_seen = Field(output_processor=TakeFirst())
    sig_dist_taken = Field(output_processor=TakeFirst())
    sig_dist_seen = Field(output_processor=TakeFirst())
    sig_clinch_taken = Field(output_processor=TakeFirst())
    sig_clinch_seen = Field(output_processor=TakeFirst())
    sig_ground_taken = Field(output_processor=TakeFirst())
    sig_ground_seen = Field(output_processor=TakeFirst())
    total_strike_taken = Field(output_processor=TakeFirst())
    total_strike_seen = Field(output_processor=TakeFirst())
    takedown_taken = Field(output_processor=TakeFirst())
    takedown_seen = Field(output_processor=TakeFirst())
    sub_seen = Field(output_processor=TakeFirst())
    reversals_taken = Field(output_processor=TakeFirst())
    ctrl_time_taken = Field(output_processor=TakeFirst())
    

class Fighter(Item):
    fighter_id = Field(output_processor=TakeFirst())
    first_name = Field(output_processor=TakeFirst())
    last_name = Field(output_processor=TakeFirst())
    nickname = Field(output_processor=TakeFirst())
    dob = Field(output_processor=TakeFirst())
    gender = Field(output_processor=TakeFirst())
    reach = Field(output_processor=TakeFirst())
    height = Field(output_processor=TakeFirst())
    weight = Field(output_processor=TakeFirst())
    stance = Field(output_processor=TakeFirst())
    status = Field(output_processor=TakeFirst())
    wins = Field(output_processor=TakeFirst())
    losses = Field(output_processor=TakeFirst())
    draws = Field(output_processor=TakeFirst())
    belt = Field(output_processor=TakeFirst())
    last_fight_date = Field(output_processor=TakeFirst())
    latest_weight_class = Field(output_processor=TakeFirst())
    create_date = Field(output_processor=TakeFirst())

class FightRanking(Item):
    fighter_1 = Field(output_processor=TakeFirst())
    fighter_2 = Field(output_processor=TakeFirst())
    fight_date = Field(output_processor=TakeFirst())
    fight_rank = Field(output_processor=TakeFirst())
    fight_id = Field(output_processor=TakeFirst())
    
