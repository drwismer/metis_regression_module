from scrapy.spiders import Spider
from scrapy.loader import ItemLoader
from scrapy.exceptions import CloseSpider
from scrapy import signals
from UFCStats.items import *
from UFCStats.tools import *
from UFCStats.queries import DatabaseQuery
from string import ascii_lowercase
from unidecode import unidecode
import datetime
import pandas as pd

class PerformanceSpider(Spider):
    name = 'performance'
    start_urls = ['http://ufcstats.com/statistics/events/completed?page=all']
    
    def __init__(self, *args, **kwargs):
        super(PerformanceSpider, self).__init__(*args, **kwargs)
        self.db_update = None
        self.DQ = DatabaseQuery()
    
    def parse(self, response):
        """
        Parse events page. Find event links in the table. Follow each link.
        """
        custom_settings = {
            'ITEM_PIPELINES': {
                'UFCStats.pipelines.UfcStatsPipeline': 400
            }
        }

        today = datetime.datetime.today().strftime('%Y-%m-%d')
        
        # Prompt user to specify whether to update new events or all events.
        event_update = None
        while event_update is None:
            try:
                event_update_type = int(input('\nSelect from the following update options. Type only the associated integer.\n'
                                              +'   (1) Only scrape and update new events not yet in the database.\n'
                                              +'   (2) Only scrape and/or update for a single, specified event.\n'
                                              +'   (3) Scrape and update all events, replacing all prior data.\n'
                                              +'   (4) Exit scraper without scraping any events.\n\n'
                                             )
                                       )
                if 1 <= event_update_type <= 4:
                    event_update = event_update_type
                else:
                    raise ValueError
            except ValueError:
                print('\n\nYou did not enter an appropriate integer. Try again.\n')
        
        
        # Determine events already in the database and filter those from event_list for spider.
        db_events = []
        event_to_update = ''
        
        if event_update == 1:
            db_events = self.DQ.query_event_list()
        elif event_update == 2:
            event_to_update = input('\n\nEnter the \'event_id\' you would like to add/update in the database.\n\n')
            self.db_update = 'YES'
        elif event_update == 4:
            raise CloseSpider('\nThe spider will not be run.')
        else:
            self.db_update = 'YES'
            
        event_list = response.css('tbody .b-statistics__table-row ::attr(href)')
        
        if db_events:
            event_list = [event for event in event_list if event.extract().split('/')[-1] not in db_events]
            if not event_list:
                raise CloseSpider('\n\nThe database already includes all past events.\n\n')
        elif event_to_update:
            event_list = [event for event in event_list if event.extract().split('/')[-1] == event_to_update]
            if not event_list:
                raise CloseSpider('\n\nThis \'event_id\' does not exist on ufcstats.com.\n\n')
        
        for event in event_list:
            yield response.follow(url=event, 
                                  callback=self.parse_event, 
                                  cb_kwargs=dict(today=today)
                                 )

    
    def parse_event(self, response, today):
        """
        Parse individual event pages. Find links to fight pages. Follow each link.
        """
        
        event_name = response.css('.b-content__title-highlight ::text').get().strip()
        event_id = response.url.split('/')[-1] #should i use this as the event id? should the id be more descriptive?
        date_and_location = response.css('.b-list__box-list-item')
        event_date = date_and_location[0].css('::text').getall()[-1].strip()
        event_date = datetime.datetime.strptime(event_date,'%B %d, %Y').strftime('%Y-%m-%d')
        location = date_and_location[1].css('::text').getall()[-1].strip().split(', ')
        event_city, event_country = location[0], location[-1]
        
        fight_list = response.xpath('//tbody//tr/@data-link').getall()
        
        num_fights = len(fight_list)
        
        weight_css = response.css('.b-fight-details__table-col ::text').getall()
        weight_classes = [w.strip() for w in weight_css if 'eight' in w][1:]
        
        # Load Event item
        if self.db_update:
            self.DQ.delete_event_record(event_id)
        
        l = ItemLoader(item=Event(), response=response)
        l.add_value('event_id', event_id)
        l.add_value('event_name', event_name)
        l.add_value('event_date', event_date)
        l.add_value('event_city', event_city)
        l.add_value('event_country', event_country)
        l.add_value('num_fights', num_fights)
        l.add_value('create_date', today)
        
        yield l.load_item()
        
        for fight, weight in zip(fight_list, weight_classes):
            yield response.follow(fight, 
                                  callback=self.parse_fight, 
                                  cb_kwargs=dict(weight=weight, 
                                                 event_id=event_id,
                                                 today=today,
                                                )
                                 )

    
    def parse_fight(self, response, weight, event_id, today):
        """
        Parse indididual fight pages for fight, round, and performance data.
        """
        
        fight_id = response.url.split('/')[-1] #should i use this as the fight id? should the id be more descriptive?
     
        fighter_names = response.css('.b-fight-details__person-name :not(p)::text').getall()
        fighter_1 = fighter_names[0].strip()
        fighter_2 = fighter_names[1].strip()
        
        fighter_ids = response.css('.b-fight-details__person-link ::attr(href)').getall()
        fighter_1_id = fighter_ids[0].split('/')[-1]
        fighter_2_id = fighter_ids[1].split('/')[-1]
        
        results = response.css('.b-fight-details__person-status ::text').getall()
        
        if results[0].strip() == 'W':
            winner = fighter_1_id #should the winner be the id or the fighter name... depends on how it will be used
        elif results[1].strip() == 'W':
            winner = fighter_2_id
        elif (results[0].strip() == 'D') & (results[1].strip() == 'D'):
            winner = 'Draw'
        else:
            winner = 'NC'
        
        bonus = response.css('.b-fight-details__fight-title ::attr(src)').getall()
        
        if bonus:
            bonus = [x.split('/')[-1][:-4] for x in bonus]
            bonus = ', '.join(bonus)
        
        method_css = response.css('.b-fight-details__text-item_first ::text').getall()
        method_css = strip_remove_blanks(method_css)
        method = method_css[1] if method_css[1].lower() != 'details:' else 'N/A'
        
        fight_info = response.css('.b-fight-details__text-item ::text').getall()
        fight_info = strip_remove_blanks(fight_info)
        
        for i in range(len(fight_info)):
            if fight_info[i] == 'Round:':
                try:
                    rd_ended = int(fight_info[i+1])
                except ValueError:
                    rd_ended = 'N/A'
            elif fight_info[i] == 'Time:':
                try:
                    time_last_rd = time_to_sec(fight_info[i+1])
                except ValueError:
                    time_last_rd = 'N/A'
            elif fight_info[i] == 'Time format:':
                try:
                    rds_sched = int(fight_info[i+1].split(' ')[0])
                except ValueError:
                    rds_sched = 'N/A'
            elif fight_info[i] == 'Referee:':
                try:
                    referee = fight_info[i+1]
                except IndexError:
                    referee = 'N/A'
        
        
        # Load Fight item
        if self.db_update:
            self.DQ.delete_fight_record(fight_id)
        
        l = ItemLoader(item=Fight(), response=response)
        l.add_value('fight_id', fight_id)
        l.add_value('event_id', event_id)
        l.add_value('weightclass', weight)
        l.add_value('rds_sched', rds_sched)
        l.add_value('method', method)
        l.add_value('rd_ended',rd_ended)
        l.add_value('time_last_rd', time_last_rd)
        l.add_value('referee', referee)
        l.add_value('bonus', bonus)
        l.add_value('fighter_1_id', fighter_1_id)
        l.add_value('fighter_2_id', fighter_2_id)
        l.add_value('winner_id', winner)
        l.add_value('create_date', today)
        
        yield l.load_item()
        
        fight_stats = response.css('.b-fight-details__table.js-fight-table')
        
        try:
            # If there is an error, round data does not exist.
            total_stats = fight_stats[0]
            sig_strike_stats = fight_stats[1]
            no_rounds = False
        except IndexError:
            # If no round data, skip creating round result items
            no_rounds = True
            pass
        
        
        if not no_rounds:
            totals_by_round = total_stats.css('.b-fight-details__table-row:not(.b-fight-details__table-row_type_head)')[1:]
            sig_strikes_by_round = sig_strike_stats.css('.b-fight-details__table-row:not(.b-fight-details__table-row_type_head)')[1:]

            for i in range(len(totals_by_round)):
                # Parse fight statistics by round and send to map_stats_to_round_result function to load item.
                rd_id = str(fight_id) + '-' + str(i+1)

                round_totals = totals_by_round[i].css('.b-fight-details__table-col ::text').getall()
                round_totals = strip_remove_blanks(round_totals)

                round_sig_strikes = sig_strikes_by_round[i].css('.b-fight-details__table-col ::text').getall()
                round_sig_strikes = strip_remove_blanks(round_sig_strikes)

                all_round_stats = round_totals[2:] + round_sig_strikes[2:]
                fighter_1_round_stats = all_round_stats[::2]
                fighter_2_round_stats = all_round_stats[1::2]

                fighter_1_round_stats = ' of  '.join(fighter_1_round_stats).split(' of ')
                fighter_2_round_stats = ' of  '.join(fighter_2_round_stats).split(' of ')

                ids = [fighter_1_id, fighter_2_id]
                ids_rev = ids[::-1]
                stats = [fighter_1_round_stats, fighter_2_round_stats]
                opp_stats = [fighter_2_round_stats, fighter_1_round_stats]


                for fighter_id, opp_id, stats, opp_stats in zip(ids, ids_rev, stats, opp_stats):
                    """
                    Take parsed round stats for a single fighter, pass to item loader, and load RoundResult item.
                    Function call occurs within for loop below, which loops through individual fighter round performances.
                    """
                    
                    
                    l = ItemLoader(item=RoundResult(), response=response)

                    # Add identifiers
                    rd_result_id = rd_id + '-' + fighter_id
                    l.add_value('rd_result_id', rd_result_id)
                    l.add_value('fighter_id', fighter_id)
                    l.add_value('opponent_id', opp_id)
                    l.add_value('rd_id', rd_id)
                    l.add_value('create_date', today)
                    
                    if self.db_update:
                        self.DQ.delete_round_result_record(rd_result_id)

                    # Add offensive stats
                    l.add_value('kd', int(stats[0]))
                    #skip total_sig_strike_land
                    #skip total_sig_strike_att
                    #skip sig_strike_perc
                    l.add_value('total_strike_land', int(stats[4]))
                    l.add_value('total_strike_att', int(stats[5]))
                    l.add_value('takedown_land', int(stats[6]))
                    l.add_value('takedown_att', int(stats[7]))
                    #skip takedown_perc
                    l.add_value('sub_att', int(stats[9]))
                    l.add_value('reversals', int(stats[10]))
                    try:
                        ctrl_time = time_to_sec(stats[11])
                        if isinstance(ctrl_time, Exception):
                            raise ctrl_time
                        else:
                            l.add_value('ctrl_time', ctrl_time)
                    except (IndexError, TypeError):
                        pass
                    #skip total_sig_strike_land
                    #skip total_sig_strike_att
                    #skip sig_strike_perc
                    l.add_value('sig_head_land', int(stats[15]))
                    l.add_value('sig_head_att', int(stats[16]))
                    l.add_value('sig_body_land', int(stats[17]))
                    l.add_value('sig_body_att', int(stats[18]))
                    l.add_value('sig_leg_land', int(stats[19]))
                    l.add_value('sig_leg_att', int(stats[20]))
                    l.add_value('sig_dist_land', int(stats[21]))
                    l.add_value('sig_dist_att', int(stats[22]))
                    l.add_value('sig_clinch_land', int(stats[23]))
                    l.add_value('sig_clinch_att', int(stats[24]))
                    l.add_value('sig_ground_land', int(stats[25]))
                    l.add_value('sig_ground_att', int(stats[26]))

                    # Add defensive stats (opponent stats)
                    l.add_value('kd_taken', int(opp_stats[0]))
                    #skip total_sig_strike_taken
                    #skip total_sig_strike_seen
                    #skip sig_strike_perc_opp
                    l.add_value('total_strike_taken', int(opp_stats[4]))
                    l.add_value('total_strike_seen', int(opp_stats[5]))
                    l.add_value('takedown_taken', int(opp_stats[6]))
                    l.add_value('takedown_seen', int(opp_stats[7]))
                    #skip takedown_perc_opp
                    l.add_value('sub_seen', int(opp_stats[9]))
                    l.add_value('reversals_taken', int(opp_stats[10]))
                    try:
                        ctrl_time_taken = time_to_sec(opp_stats[11])
                        if isinstance(ctrl_time_taken, Exception):
                            raise ctrl_time_taken
                        else:
                            l.add_value('ctrl_time_taken', ctrl_time_taken)
                    except (IndexError, TypeError):
                        pass
                    #skip total_sig_strike_taken
                    #skip total_sig_strike_seen
                    #skip sig_strike_perc_opp
                    l.add_value('sig_head_taken', int(opp_stats[15]))
                    l.add_value('sig_head_seen', int(opp_stats[16]))
                    l.add_value('sig_body_taken', int(opp_stats[17]))
                    l.add_value('sig_body_seen', int(opp_stats[18]))
                    l.add_value('sig_leg_taken', int(opp_stats[19]))
                    l.add_value('sig_leg_seen', int(opp_stats[20]))
                    l.add_value('sig_dist_taken', int(opp_stats[21]))
                    l.add_value('sig_dist_seen', int(opp_stats[22]))
                    l.add_value('sig_clinch_taken', int(opp_stats[23]))
                    l.add_value('sig_clinch_seen', int(opp_stats[24]))
                    l.add_value('sig_ground_taken', int(opp_stats[25]))
                    l.add_value('sig_ground_seen', int(opp_stats[26]))
                    
                    yield l.load_item()
            

        for i in range(int(rd_ended)):
            # Load Round item
            if i+1 == int(rd_ended):
                rd_length = time_last_rd
            else:
                rd_length = 300

            rd_id = str(fight_id) + '-' + str(i+1)
            
            if self.db_update:
                self.DQ.delete_round_record(rd_id)
            
            l = ItemLoader(item=Round(), response=response)
            
            l.add_value('rd_id', rd_id)
            l.add_value('fight_id', fight_id)
            l.add_value('rd_num', i+1)
            l.add_value('rd_length', rd_length)
            l.add_value('create_date', today)
            
            yield l.load_item()
        

class FighterSpider(Spider):
    name = 'fighter'
    start_urls = ['http://www.ufcstats.com/statistics/fighters']
    
    def __init__(self, *args, **kwargs):
        super(FighterSpider, self).__init__(*args, **kwargs)
        self.fighter_list = []
    
    def parse(self, response):
        """
        Create list of last name by letter links and follow each.
        """
        custom_settings = {
            'ITEM_PIPELINES': {
                'UFCStats.pipelines.UfcStatsPipeline': 400
            }
        }
        
        # Prompt user to specify whether to update all fighters or to provide an event number.
        event_update = None
        while event_update is None:
            try:
                event_update_type = int(input('\nSelect from the following update options. Type only the associated integer.\n'
                                        +'   (1) Only scrape and update fighters who participated in a specified event.\n'
                                        +'   (2) Scrape and update all fighters, replacing all prior data.\n'
                                        +'   (3) Exit scraper without scraping any fighters.\n\n'
                                             )
                                       )
                if 1 <= event_update_type <= 3:
                    event_update = event_update_type
                else:
                    raise ValueError
            except ValueError:
                print('\n\nYou did not enter an appropriate integer. Try again.\n')
        
        
        if event_update == 1:
            event_id = input('\nEnter the \'event_id\' as shown in the \'events\' Postgres table.\n\n')
            try:
                DQ = DatabaseQuery()
                db_events = DQ.query_event_list()
                if event_id not in db_events:
                    raise ValueError
                else:
                    yield response.follow(url='http://www.ufcstats.com/event-details/' + event_id,
                                          callback=self.parse_event)
            except ValueError:
                print('The \'event_id\' provided is not in the database. The spider will now close.')
                raise CloseSpider()
        elif event_update == 3:
            raise CloseSpider('\nThe spider will not be run.')
        
        
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        
        last_name_letter_links = []
      
        
        for i in ascii_lowercase:
            last_name_letter_links.append(self.start_urls[0] + '?char={}&page=all'.format(i))

        for link in last_name_letter_links:
            yield response.follow(url=link, 
                                  callback=self.parse_letter, 
                                  cb_kwargs=dict(today=today)
                                 )
    
    
    def parse_event(self, response):
        """
        Generate list of fighters who participated in a specified event.
        """
        fighter_links = response.css('.b-fight-details__table-text .b-link ::attr(href)').extract()
        self.fighter_list = [x.split('/')[-1] for x in fighter_links]
    
    
    def parse_letter(self, response, today):
        """
        Parse individual last name by letter pages.
        """
        
        fighters = response.css('.b-statistics__table-row')[2:]  # Leave out header and blank row
        
        # Exclude all fighters who did not participate in specified event (if not running a full update).
        if self.fighter_list:
            fighters = [x for x in fighters if x.css('::attr(href)').get().split('/')[-1] in self.fighter_list]
        
        for i in range(len(fighters)):
            details = fighters[i].css('.b-statistics__table-col')
            
            # Check if belt icon exists in fighter row.
            belt = ''
            try:
                if details[10].css('::attr(src)').get().split('/')[-1].split('.')[0] == 'belt':
                    belt = 'X'
                else:
                    belt = ''
            except AttributeError:
                pass
            
            details = [''.join(x.css('::text').getall()).strip() for x in details]
            
            first_name = details[0]
            last_name = details[1]
            nickname = details[2]
            
            try:
                height = details[3].split('\' ') 
                inches = int(height[1][:-1])
                feet = int(height[0])
                height_inches = feet*12 + inches
            except (IndexError, TypeError, ValueError):
                height_inches = None
                
            try:
                weight = int(details[4].split(' ')[0])
            except (IndexError, TypeError, ValueError):
                weight = None
            
            if details[5] == '--':
                reach = None
            else:
                try:
                    reach = int(float(details[5][:-1]))
                except (IndexError, TypeError, ValueError):
                    reach - None
            
            stance = str(details[6])
            wins = int(details[7])
            losses = int(details[8])
            draws = int(details[9])
            
            fighter_link = fighters[i].css('.b-statistics__table-col ::attr(href)').get()
            
            fighter_id = fighter_link.split('/')[-1]
            
            yield response.follow(url=fighter_link,
                                  callback=self.parse_fighter,
                                  cb_kwargs=dict(first_name=first_name,
                                                 last_name=last_name,
                                                 nickname=nickname,
                                                 height=height_inches,
                                                 weight=weight,
                                                 reach=reach,
                                                 stance=stance,
                                                 wins=wins,
                                                 losses=losses,
                                                 draws=draws,
                                                 belt=belt,
                                                 fighter_id=fighter_id,
                                                 today=today
                                                )
                                 )
            
            
    
    
    def parse_fighter(self, response, first_name, last_name, nickname, height, weight, reach,
                      stance, wins, losses, draws, belt, fighter_id, today):
        """
        Parse fighter link to find date of birth. Load fighter item.
        """
        
        boxes = response.css('.b-list__box-list')[0]  # box_1
        boxes_text = boxes.xpath('//ul//li/text()').getall()
        
        try:
            dob = datetime.datetime.strptime(boxes_text[9].strip(),'%b %d, %Y').strftime('%Y-%m-%d')
        except ValueError:
            dob = None
        
        # Delete old record of fighter before loading new record.
        DQ = DatabaseQuery()
        DQ.delete_fighter_record(fighter_id)
        
        last_fight = DQ.query_last_fight(fighter_id).first()
        
        last_fight_date = ''
        latest_weight_class = ''
        gender = ''
        try:
            last_fight_date = last_fight[-1]
            latest_weight_class = last_fight[1]
            if 'Women' in last_fight[1]:
                gender = 'F'
            else:
                gender = 'M'
        except:
            pass
        
        l = ItemLoader(item=Fighter(), response=response)
        
        l.add_value('fighter_id', fighter_id)
        l.add_value('first_name', first_name)
        l.add_value('last_name', last_name)
        l.add_value('nickname', nickname)
        l.add_value('dob', dob)
        l.add_value('reach', reach)
        l.add_value('height', height)
        l.add_value('weight', weight)
        l.add_value('stance', stance)
        l.add_value('wins', wins)
        l.add_value('losses', losses)
        l.add_value('draws', draws)
        l.add_value('belt', belt)
        l.add_value('last_fight_date', last_fight_date)
        l.add_value('latest_weight_class', latest_weight_class)
        l.add_value('gender', gender)
        l.add_value('create_date', today)
        
        yield l.load_item()      
    
        
class TapologySpider(Spider):
    name = 'tapology'
    start_urls = ['https://www.tapology.com/rankings/all-time-greatest-fights-in-mma-and-ufc-history?ranking=14']

    
    def __init__(self, *args, **kwargs):
        super(TapologySpider, self).__init__(*args, **kwargs)
        self.last_rank = 0
        self.not_found = 0
        self.not_found_list = ''
        self.more_than_one = 0
        self.more_than_one_list = ''
        self.DQ = DatabaseQuery()
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TapologySpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    
    def spider_closed(self, spider):
        """
        Print summary of parsing issues upon close.
        """
        print('-'*50)
        print('Fights not found: ' + str(self.not_found))
        print(self.not_found_list)
        print('-'*50)
        print('More than one matching fight_id: ' + str(self.more_than_one))
        print(self.more_than_one_list)
        print('-'*50)
        
    def parse(self, response):
        """
        Wipe out 'tapology_rank' column. Create list of page links and follow each.
        """
        custom_settings = {
            'ITEM_PIPELINES': {
                'UFCStats.pipelines.UfcStatsPipeline': 400
            }
        }
        
        self.DQ.clear_fight_rank()
        
        rank_links = ['https://www.tapology.com/rankings/all-time-greatest-fights-in-mma-and-ufc-history?ranking=14']
        link_root = 'https://www.tapology.com/rankings/all-time-greatest-fights-in-mma-and-ufc-history?page='
                
        for i in range(2,7):
            new_link = link_root + str(i) + '&ranking=14'
            rank_links.append(new_link)
        
        for i in range(len(rank_links)):
            yield response.follow(url=rank_links[i], callback=self.parse_rank_page)

    
    def parse_rank_page(self, response):
        """
        Parse ranking page, find specified number of UFC events, and follow each link to the fight page
        """
        
        rankings = response.css('.rankingItemsItem')
        
        for fight in rankings:
            event_name = fight.css('.right ::text').get()

            if ('ufc' in event_name.lower()) or ('ultimate fighter') in event_name.lower():
                self.last_rank += 1
                fight_link = fight.css('::attr(href)')[-1]
                fight_rank = int(fight.css('.rankingItemsItemRank ::text').get())

                yield response.follow(url=fight_link, 
                                      callback=self.parse_fight,
                                      cb_kwargs=dict(fight_rank=fight_rank)
                                     )

    def parse_fight(self, response, fight_rank):
        """
        Parse the fight page to get fighter names and the date of the fight. Update fight item
        """
        
        fighter_names = response.css('.fighterNames ::text').getall()
        fighter_1 = fighter_names[3].split(' ')
        fighter_2 = fighter_names[7].split(' ')
        
        fight_details = response.css('.borderTop ::text').getall()
        date = fight_details[3]
        date = date.replace('\n', '').replace('\xa0', '').replace('|', '').replace(' ', '').replace('.', '-')
        
        fight_id = self.DQ.query_fight_id(fighter_1, fighter_2, date)
        
        if len(fight_id) != 1:
            details = ('Rank: ' + str(fight_rank) + ', Date: ' + date 
                       + ', Fighters: '+ fighter_names[3] + ', ' + fighter_names[7] +' ('+f1_last+') '+'('+f2_last+')\n'
                      )
            if len(fight_id) == 0:
                self.not_found += 1
                self.not_found_list += details
            else:
                self.more_than_one += 1
                self.more_than_one_list += details
        else:
            self.DQ.update_fight_rank(fight_id[0], fight_rank)

        
class DecisionSpider(Spider):
    name = 'decision'
    start_urls = ['http://mmadecisions.com/decisions-by-event/']
    
    def __init__(self, *args, **kwargs):
        super(DecisionSpider, self).__init__(*args, **kwargs)
        self.cutoff_date = datetime.datetime(2010, 1, 1).date()
        self.not_found = 0
        self.not_found_list = ''
        self.more_than_one = 0
        self.more_than_one_list = ''
        self.DQ = DatabaseQuery()
    

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(DecisionSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    
    def spider_closed(self, spider):
        """
        Print summary of parsing issues upon close.
        """
        print('-'*50)
        print('Fights not found: ' + str(self.not_found))
        print(self.not_found_list)
        print('-'*50)
        print('More than one matching fight_id: ' + str(self.more_than_one))
        print(self.more_than_one_list)
        print('-'*50)
        

    def parse(self, response):
        """
        Find max date where decision is captured. Scrape all mmadecisions.com UFC events past that date.
        """
        custom_settings = {
            'ITEM_PIPELINES': {
                'UFCStats.pipelines.UfcStatsPipeline': 400
            }
        }
        
        # Prompt user to specify whether to update new events or all events.
        event_update = None
        while event_update is None:
            try:
                event_update_type = int(input('\nSelect from the following update options. Type only the associated integer.\n'
                                              +'   (1) Only scrape and update decision data for events not yet described in the database.\n'
                                              +'   (2) Scrape and update all events, replacing all prior data.\n'
                                              +'   (3) Exit scraper without scraping any events.\n\n'
                                             )
                                       )
                if 1 <= event_update_type <= 3:
                    event_update = event_update_type
                else:
                    raise ValueError
            except ValueError:
                print('\n\nYou did not enter an appropriate integer. Try again.\n')
        
        if event_update == 1:
            latest_date = self.DQ.query_latest_decision_date()
            self.cutoff_date = datetime.datetime.strptime(latest_date, '%Y-%m-%d').date()
        elif event_update == 2:
            pass
        elif event_update == 3:
            raise CloseSpider('\nThe spider will not be run.')
        
        year_links = []
        link_root = 'http://mmadecisions.com/decisions-by-event/'
        
        
        
        for i in range(self.cutoff_date.year, datetime.datetime.today().year + 1):
            new_link = link_root + str(i) + '/'
            year_links.append(new_link)
        
        for i in range(len(year_links)):
            yield response.follow(url=year_links[i], callback=self.parse_year_page)
    
    
    def parse_year_page(self, response):
        """
        Parse ranking page, find specified number of UFC events, and follow each link to the fight page
        """
        
        events = response.css('.decision')
        
        for event in events:
            event_name = event.css('.list ::text').get()
            event_date = datetime.datetime.strptime(event.css('.list-center ::text').get().replace('\xa0', ''),
                                                    '%b %d, %Y').date()
            
            if (('ufc' in event_name.lower()) or (('ultimate fighter') in event_name.lower()) \
                or ('ufn' in event_name.lower())):
                
                if event_date > self.cutoff_date:
                    event_link = event.css('::attr(href)')[-1]
                    yield response.follow(url=event_link, 
                                          callback=self.parse_event,
                                          cb_kwargs=dict(event_date=event_date)
                                         )
    
    
    def parse_event(self, response, event_date):
        """
        Parse event page, getting details for decisions for each fight.
        """
        
        fight_table = response.xpath('//body//div//table')[-1].xpath('//table')[-1]
        fights = fight_table.xpath('//tr')[5:-1]
        
        text_to_replace = ['\r', '\t', '\n', '\xa0']
        
        for fight in fights:
            # Get text, remove unwanted characters, condense list to relevant data
            try:
                text = fight.css('::text').getall()

                for sub in text_to_replace:
                    text = [string.replace(sub, '') for string in text]

                text = [item for item in text if item.strip()]

                # Get fighter names
                last_names = text[0].split('def.')

                if len(last_names) < 2:
                    last_names = text[0].split('drew with')

                fighter_1_last = last_names[0].strip()
                fighter_2_last = last_names[1].strip()

                date = event_date.strftime('%Y-%m-%d')

                # Query for fight_id in postgres, and if found, get judges scores and update the db
                fight_id = self.DQ.query_fight_id(fighter_1_last, fighter_2_last, date, last_only=True)

                if len(fight_id) != 1:
                    details = ('Date: ' + date + ', Fighters: '+ fighter_1_last + ', ' + fighter_2_last)
                    if len(fight_id) == 0:
                        self.not_found += 1
                        self.not_found_list += (details + '\n')
                    else:
                        self.more_than_one += 1
                        self.more_than_one_list += (details + '\n')
                else:
                    scores = [item for item in text if ' - ' in item]
                    fighter_positions = self.DQ.query_last_names(fight_id[0])

                    # Determine if fighter_1 in mmadecisions matches fighter_1 in db
                    fighter1 = unidecode(fighter_1_last).lower().replace(r"'", r"''") == fighter_positions[0].lower()
                    fighter2 = unidecode(fighter_2_last).lower().replace(r"'", r"''") == fighter_positions[1].lower()
                    correct_position = (fighter1 or fighter2)

                    # Split judge scores into lists of integers
                    judge1 = scores[0].split(' - ')
                    judge2 = scores[1].split(' - ')
                    judge3 = scores[2].split(' - ')
                    
                    # Assign judge scores to list to be passed to db
                    if correct_position:
                        judge1_fighter1, judge1_fighter2 = int(judge1[0]), int(judge1[1])
                        judge2_fighter1, judge2_fighter2 = int(judge2[0]), int(judge2[1])
                        judge3_fighter1, judge3_fighter2 = int(judge3[0]), int(judge3[1])
                    else:
                        judge1_fighter2, judge1_fighter1 = int(judge1[0]), int(judge1[1])
                        judge2_fighter2, judge2_fighter1 = int(judge2[0]), int(judge2[1])
                        judge3_fighter2, judge3_fighter1 = int(judge3[0]), int(judge3[1])

                    scores_upload = [judge1_fighter1, judge1_fighter2,
                                     judge2_fighter1, judge2_fighter2,
                                     judge3_fighter1, judge3_fighter2
                                    ]

                    self.DQ.update_judge_scores(fight_id[0], scores_upload)
                    
                    # Determine fight link and parse for media scores
                    fight_link = 'http://mmadecisions.com/' + fight.css('::attr(href)').get().strip()
                    yield response.follow(url=fight_link, 
                                          callback=self.parse_fight,
                                          cb_kwargs=dict(fight_id=fight_id[0],
                                                         fighter_1_last=fighter_1_last,
                                                         fighter_2_last=fighter_2_last,
                                                         correct_position=correct_position
                                                        )
                                         )
            
            except IndexError:
                # Code sometimes captures blank rows from mmadecisions. Pass on these rows.
                continue
    

            
    def parse_fight(self, response, fight_id, fighter_1_last, fighter_2_last, correct_position):
        """
        Get judges' round scores and media scores from fight page. Determine if there were any
        point deductions. Update postgres database.
        """
        
        media_decisions = (response.xpath('//body/div')[0].xpath('table')[-1].xpath('tr')[0].xpath('td')[0]\
                           .xpath('table')[1].xpath('tr/td')[0].css('.decision'))
        
        
        # Create dataframe to hold media scores by fighter
        columns = [fighter_1_last, fighter_2_last]
        media_scores = pd.DataFrame(columns=columns)
        
        for decision in media_decisions:
            # Populate dataframe with media scores
            scores = decision.xpath('td')[1].css('::text').getall()[1].split('-')
            winner = decision.xpath('td')[-1].css('::text').getall()[0]
            
            if winner.lower() == 'draw':
                f1_index = 0
                f2_index = 0
            elif winner.lower() == fighter_1_last.lower():
                f1_index = 0
                f2_index = 1
            else:
                f1_index = 1
                f2_index = 0
            
            media_scores = media_scores.append({fighter_1_last: int(scores[f1_index]),
                                                fighter_2_last: int(scores[f2_index])},
                                               ignore_index=True
                                              )
        
        
        # Calculate mean scores by fighter and number of media scores and pass to postgres db
        mean_scores = list(media_scores.mean(axis=0))
        count_scores = len(media_scores)
        
        if not correct_position:
            mean_scores = mean_scores[::-1]
        
        self.DQ.update_media_scores(fight_id=fight_id,
                                    media_scores=mean_scores,
                                    media_count=count_scores
                                   )
        
        
        # Get table with judge scoring and deduction details
        combined_table = (response.xpath('//body/div')[0].xpath('table')[1].xpath('tr')[0].xpath('td')[0].\
                          xpath('table')[0])
        
        
        # Get point deduction details, save to postgres db if deductions exist
        deductions = combined_table.xpath('tr')[-1].css('::text').getall()
        
        deductions = [x.strip().replace("'", '') for x in deductions if x.strip()]
        
        if deductions:
            deduction_str = deductions[0]
            
            for i in range(1,len(deductions)):
                if i%2==0:
                    deduction_str = '\n'.join([deduction_str, deductions[i]])
                else:
                    deduction_str = ' '.join([deduction_str, deductions[i]])
            
            self.DQ.update_deductions(fight_id, deduction_str)
        
        
        # Get round scoring details and create lists to be populated
        round_scoring = combined_table.xpath('tr')[-2].xpath('td/table/tr/td')
        
        judge_names = []
        judge1_fighter1 = []
        judge1_fighter2 = []
        judge2_fighter1 = []
        judge2_fighter2 = []
        judge3_fighter1 = []
        judge3_fighter2 = []
        
        for i in range(len(round_scoring)):
            # Loop through each judge, save name to list
            table = round_scoring[i].xpath('table')
            
            judge_name_details = table.xpath('tr')[0].css('::text').getall()
            
            judge_name = unidecode([x.strip().replace('\xa0', ' ').replace("'", '')\
                                    for x in judge_name_details if x.strip()
                                   ][0]
                                  )
            
            judge_names.append(judge_name)
            
            # Loop through the judge's round scores, save scores to lists for upload to postgres db
            round_scores = table.css('.decision ::text').getall()
            round_scores = [x.strip() for x in round_scores if x.strip()]

            for j in range(0, len(round_scores), 3):
                if i==0:
                    judge_round_scores(round_scores, judge1_fighter1, judge1_fighter2, j, correct_position)
                elif i==1:
                    judge_round_scores(round_scores, judge2_fighter1, judge2_fighter2, j, correct_position)
                elif i==2:
                    judge_round_scores(round_scores, judge3_fighter1, judge3_fighter2, j, correct_position)
                

        # Upload scores and judge names to postgres db
        scores_upload = [judge1_fighter1, judge1_fighter2,
                         judge2_fighter1, judge2_fighter2,
                         judge3_fighter1, judge3_fighter2
                        ]
        
        self.DQ.update_judge_names(fight_id, judge_names)
        self.DQ.update_round_scores(fight_id, scores_upload)