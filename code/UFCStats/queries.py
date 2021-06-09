from itemadapter import ItemAdapter
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from UFCStats.models import *
from unidecode import unidecode
from itertools import product
import pandas as pd
import datetime

class DatabaseQuery:
    def __init__(self):
        """
        Initializes db connection and sessionmaker.
        """
        self.engine = UFCStats.models.db_connect()
        self.Session = sessionmaker(bind=self.engine)
    
    
    
    # Queries for spiders
    
    def query_event_list(self):
        db_events = self.engine.execute('SELECT event_id FROM events')
        return [x.event_id for x in db_events]
    
    
    def query_last_fight(self, fighter_id):
        """
        Determines a fighter's most recent fight and returns details.
        """
        last_fight = self.engine.execute('SELECT fights.event_id, weightclass, fighter_1_id, fighter_2_id, event_date '
                                         + 'FROM fights '
                                         + 'INNER JOIN events ON fights.event_id=events.event_id  '
                                         + 'WHERE fighter_1_id=\''+fighter_id+'\' or fighter_2_id=\''+fighter_id+'\' '
                                         + 'ORDER BY event_date DESC '
                                         + 'LIMIT 1'
                                        )
        return last_fight

    def query_fight_id(self, fighter_1, fighter_2, date, last_only=False):
        """
        Finds the 'fight_id' in the 'fights' table with given date and fighter info.
        """
        
        # Sometimes special characters must be converted to ascii. Account for potential spaces in first/last names.
        if last_only:
            f1_last_1 = unidecode(fighter_1).lower().replace(r"'", r"''")
            f2_last_1 = unidecode(fighter_2).lower().replace(r"'", r"''")
            f1_last_names = [f1_last_1]
            f2_last_names = [f2_last_1]
        else:
            f1_first_1 = unidecode(fighter_1[0]).lower().replace(r"'", r"''")
            f1_first_2 = unidecode(' '.join(fighter_1[0:1])).replace(r"'", r"''")
            f1_last_1 = unidecode(fighter_1[-1]).lower().replace(r"'", r"''")
            f1_last_2 = unidecode(' '.join(fighter_1[1:])).lower().replace(r"'", r"''")
            f2_first_1 = unidecode(fighter_2[0]).lower().replace(r"'", r"''")
            f2_first_2 = unidecode(' '.join(fighter_2[0:1])).replace(r"'", r"''")
            f2_last_1 = unidecode(fighter_2[-1]).lower().replace(r"'", r"''")
            f2_last_2 = unidecode(' '.join(fighter_2[1:])).lower().replace(r"'", r"''")        
            f1_last_names = [f1_last_1, f1_last_2]
            f2_last_names = [f2_last_1, f2_last_2]
            f1_first_names = [f1_first_1, f1_first_2]
            f2_first_names = [f2_first_1, f2_first_2]

        # Sometimes dates are off by a day on different websites. Create a range of three dates to loop through as needed.
        date_format = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        dates = [date_format.strftime('%Y-%m-%d'),
                 (date_format + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                 (date_format - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                ]
        
        
        fight_id = []
        
        sql_selection = ('SELECT fights.fight_id '
                         + 'FROM fights '
                         + 'INNER JOIN events ON fights.event_id=events.event_id '
                         + 'INNER JOIN fighters fighter_1  ON fights.fighter_1_id=fighter_1.fighter_id '
                         + 'INNER JOIN fighters fighter_2  on fights.fighter_2_id=fighter_2.fighter_id '
                        )

        # On the first pass, we will try to use the combination of fighters' last names (two options) and the date.
        for x in product(f1_last_names, f2_last_names, dates):
            fight_id = self.engine.execute(sql_selection
                                           + 'WHERE ((lower(fighter_1.last_name)=\''+x[0]+'\' '
                                           + 'AND lower(fighter_2.last_name)=\''+x[1]+'\') '
                                           + 'OR (lower(fighter_1.last_name)=\''+x[1]+'\' '
                                           + 'AND lower(fighter_2.last_name)=\''+x[0]+'\')) '
                                           + 'AND events.event_date=\''+x[2]+'\''
                                          )
            fight_id = [x.fight_id for x in fight_id]
            if fight_id:
                break

        # On the second pass, we will try fighter_1's name only. We will use the full name.
        if (not fight_id and not last_only):
            for x in product(f1_first_names, f1_last_names, dates):
                fight_id = self.engine.execute(sql_selection
                                               + 'WHERE ((lower(fighter_1.last_name)=\''+x[1]+'\' '
                                               + 'AND lower(fighter_1.first_name)=\''+x[0]+'\') '
                                               + 'OR (lower(fighter_1.last_name)=\''+x[1]+'\' '
                                               + 'AND lower(fighter_1.first_name)=\''+x[0]+'\')'
                                               + 'OR (lower(fighter_2.last_name)=\''+x[1]+'\' '
                                               + 'AND lower(fighter_2.first_name)=\''+x[0]+'\')'
                                               + 'OR (lower(fighter_2.last_name)=\''+x[1]+'\' '
                                               + 'AND lower(fighter_2.first_name)=\''+x[0]+'\'))'
                                               + 'AND events.event_date=\''+x[2]+'\''
                                              )
                fight_id = [x.fight_id for x in fight_id]
                if fight_id:
                    break

        # On the third pass, we will try fighter_2's name only. We will use the full name.
        if (not fight_id and not last_only):
            for x in product(f2_first_names, f2_last_names, dates):
                fight_id = self.engine.execute(sql_selection
                                               + 'WHERE ((lower(fighter_1.last_name)=\''+x[1]+'\' '
                                               + 'AND lower(fighter_1.first_name)=\''+x[0]+'\') '
                                               + 'OR (lower(fighter_1.last_name)=\''+x[1]+'\' '
                                               + 'AND lower(fighter_1.first_name)=\''+x[0]+'\')'
                                               + 'OR (lower(fighter_2.last_name)=\''+x[1]+'\' '
                                               + 'AND lower(fighter_2.first_name)=\''+x[0]+'\')'
                                               + 'OR (lower(fighter_2.last_name)=\''+x[1]+'\' '
                                               + 'AND lower(fighter_2.first_name)=\''+x[0]+'\'))'
                                               + 'AND events.event_date=\''+x[2]+'\''
                                              )
                fight_id = [x.fight_id for x in fight_id]
                if fight_id:
                    break


        # On the foourth pass, we will try flipping the first and last names, as is sometimes done with Chinese names, for example.
        if (not fight_id and not last_only):
            for x in product(f1_first_names, f1_last_names, dates):
                fight_id = self.engine.execute(sql_selection
                                               + 'WHERE ((lower(fighter_1.last_name)=\''+x[0]+'\' '
                                               + 'AND lower(fighter_1.first_name)=\''+x[1]+'\') '
                                               + 'OR (lower(fighter_1.last_name)=\''+x[0]+'\' '
                                               + 'AND lower(fighter_1.first_name)=\''+x[1]+'\')'
                                               + 'OR (lower(fighter_2.last_name)=\''+x[0]+'\' '
                                               + 'AND lower(fighter_2.first_name)=\''+x[1]+'\')'
                                               + 'OR (lower(fighter_2.last_name)=\''+x[0]+'\' '
                                               + 'AND lower(fighter_2.first_name)=\''+x[1]+'\'))'
                                               + 'AND events.event_date=\''+x[2]+'\''
                                              )
                fight_id = [x.fight_id for x in fight_id]
                if fight_id:
                    break

        # Now we do the same, flipping names for fighter_2.
        if (not fight_id and not last_only):
            for x in product(f2_first_names, f2_last_names, dates):
                fight_id = self.engine.execute(sql_selection
                                               + 'WHERE ((lower(fighter_1.last_name)=\''+x[0]+'\' '
                                               + 'AND lower(fighter_1.first_name)=\''+x[1]+'\') '
                                               + 'OR (lower(fighter_1.last_name)=\''+x[0]+'\' '
                                               + 'AND lower(fighter_1.first_name)=\''+x[1]+'\')'
                                               + 'OR (lower(fighter_2.last_name)=\''+x[0]+'\' '
                                               + 'AND lower(fighter_2.first_name)=\''+x[1]+'\')'
                                               + 'OR (lower(fighter_2.last_name)=\''+x[0]+'\' '
                                               + 'AND lower(fighter_2.first_name)=\''+x[1]+'\'))'
                                               + 'AND events.event_date=\''+x[2]+'\''
                                              )
                fight_id = [x.fight_id for x in fight_id]
                if fight_id:
                    break

        return fight_id
    
    def query_last_names(self, fight_id):
        """
        Given a fight_id, return the last names of fighter_1 and fighter_2
        """
        last_names = self.engine.execute('SELECT fighter1.last_name AS f1_last, fighter2.last_name AS f2_last '
                                         + 'FROM fights '
                                         + 'INNER JOIN fighters fighter1 ON fights.fighter_1_id=fighter1.fighter_id '
                                         + 'INNER JOIN fighters fighter2 ON fights.fighter_2_id=fighter2.fighter_id '
                                         + 'WHERE fights.fight_id = \''+fight_id+'\''
                                        )
        
        return last_names.fetchone()
    
    def query_latest_decision_date(self):
        """
        Query for the date of the most recent event with decision data.
        """
        latest_date = self.engine.execute('SELECT e.event_date '
                                          + 'FROM events AS e '
                                          + 'INNER JOIN fights ON e.event_id=fights.event_id '
                                          + 'WHERE fights.judge1_fighter1 > 0 '
                                          + 'ORDER BY e.event_date DESC '
                                          + 'LIMIT 1'
                                         )
        
        return latest_date.fetchone()[0]
    
    
    
    # Updating records
    
    def update_fight_rank(self, fight_id, rank):
        self.engine.execute('UPDATE fights SET tapology_rank=\'' + str(rank) + '\' WHERE fight_id=\'' + fight_id + '\'')

    def update_judge_scores(self, fight_id, scores):
        try:
            update_command = 'UPDATE fights SET {}=\'{}\' WHERE fight_id=\'{}\''
            self.engine.execute(update_command.format('judge1_fighter1', scores[0], fight_id))
            self.engine.execute(update_command.format('judge1_fighter2', scores[1], fight_id))
            self.engine.execute(update_command.format('judge2_fighter1', scores[2], fight_id))
            self.engine.execute(update_command.format('judge2_fighter2', scores[3], fight_id))
            self.engine.execute(update_command.format('judge3_fighter1', scores[4], fight_id))
            self.engine.execute(update_command.format('judge3_fighter2', scores[5], fight_id))
        except:
            # Pass if the update fails
            pass
    
    def update_media_scores(self, fight_id, media_scores, media_count):
        try:
            update_command = 'UPDATE fights SET {}=\'{}\' WHERE fight_id=\'{}\''
            self.engine.execute(update_command.format('media_fighter1', media_scores[0], fight_id))
            self.engine.execute(update_command.format('media_fighter2', media_scores[1], fight_id))
            self.engine.execute(update_command.format('media_count', media_count, fight_id))
        except:
            # Pass if the update fails
            pass

    def update_deductions(self, fight_id, deductions):
        try:
            update_command = 'UPDATE fights SET {}=\'{}\' WHERE fight_id=\'{}\''
            self.engine.execute(update_command.format('deductions', deductions, fight_id))
        except:
            # Pass if the update fails
            pass
        
    def update_judge_names(self, fight_id, judge_names):
        try:
            update_command = 'UPDATE fights SET {}=\'{}\' WHERE fight_id=\'{}\''
            self.engine.execute(update_command.format('judge1', judge_names[0], fight_id))
            self.engine.execute(update_command.format('judge2', judge_names[1], fight_id))
            self.engine.execute(update_command.format('judge3', judge_names[2], fight_id))
        except:
            # Pass if the update fails
            pass
        
        
    def update_round_scores(self, fight_id, scores):
        try:
            update_command = 'UPDATE rounds SET {}=\'{}\' WHERE rd_id=\'{}\''
            for i in range(len(scores[0])):
                self.engine.execute(update_command.format('judge1_fighter1', scores[0][i], fight_id+'-'+str(i+1)))
                self.engine.execute(update_command.format('judge1_fighter2', scores[1][i], fight_id+'-'+str(i+1)))
                self.engine.execute(update_command.format('judge2_fighter1', scores[2][i], fight_id+'-'+str(i+1)))
                self.engine.execute(update_command.format('judge2_fighter2', scores[3][i], fight_id+'-'+str(i+1)))
                self.engine.execute(update_command.format('judge3_fighter1', scores[4][i], fight_id+'-'+str(i+1)))
                self.engine.execute(update_command.format('judge3_fighter2', scores[5][i], fight_id+'-'+str(i+1)))
        except:
            # Pass if the update fails
            pass
    
    
    
    # Clearing and deleting records
    
    def clear_fight_rank(self):
        self.engine.execute('UPDATE fights SET tapology_rank=NULL')
        
    def delete_event_record(self, event_id):
        self.engine.execute('DELETE FROM events WHERE event_id=\'' + event_id + '\'')
    
    def delete_fight_record(self, fight_id):
        self.engine.execute('DELETE FROM fights WHERE fight_id=\'' + fight_id + '\'')
    
    def delete_round_record(self, rd_id):
        self.engine.execute('DELETE FROM rounds WHERE rd_id=\'' + rd_id + '\'')
    
    def delete_round_result_record(self, rd_result_id):
        self.engine.execute('DELETE FROM round_results WHERE rd_result_id=\'' + rd_result_id + '\'')
    
    def delete_fighter_record(self, fighter_id):
        self.engine.execute('DELETE FROM fighters WHERE fighter_id=\'' + fighter_id + '\'')
        
    
    
    # Linear Regression Model Queries
    
    def get_round_results(self):
        query = self.engine.execute('SELECT rd_id, fighter_id, kd, sig_head_land, sig_body_land, sig_leg_land, sig_dist_land, sig_clinch_land, '
                                    + 'sig_ground_land, total_strike_land, total_strike_att, takedown_land, takedown_att, sub_att, '
                                    + 'reversals, ctrl_time, kd_taken, sig_head_taken, sig_body_taken, sig_leg_taken, sig_dist_taken, ' 
                                    + 'sig_clinch_taken, sig_ground_taken, total_strike_taken, total_strike_seen, takedown_taken, '
                                    + 'takedown_seen, sub_seen, reversals_taken, ctrl_time_taken '
                                    + 'FROM round_results'
                                   )
        return query
    
    def get_fights(self):
        """
        Only returns fights that ended in a decision.
        """
        query = self.engine.execute('SELECT fight_id, rds_sched, method, fighter_1_id, fighter_2_id, judge1, judge2, judge3, judge1_fighter1, '
                                    + 'judge1_fighter2, judge2_fighter1, judge2_fighter2, judge3_fighter1, judge3_fighter2, '
                                    + 'media_fighter1, media_fighter2, media_count '
                                    + 'FROM fights '
                                    + 'WHERE method like \'Decision%%\' AND judge1_fighter1 > 0'
                                   )
        return query
    
    def get_fighter_names(self):
        query = self.engine.execute('SELECT fighter_id, first_name, last_name '
                                    + 'FROM fighters'
                                   )
        return query
        
    def get_event_dates(self):
        query = self.engine.execute('SELECT event_id, event_date '
                                    + 'FROM events'
                                   )
        return query
    
    def get_round_scoring(self):
        """
        Only returns round data for fights that ended in a decision.
        """
        query = self.engine.execute('SELECT rd_id, fight_id, rd_num, judge1_fighter1, judge1_fighter2, judge2_fighter1, judge2_fighter2, '
                                    +' judge3_fighter1, judge3_fighter2 '
                                    + 'FROM rounds '
                                    + 'WHERE judge1_fighter1 > 0'
                                   )
        return query
        