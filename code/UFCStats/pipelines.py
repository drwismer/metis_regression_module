# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from itemadapter import ItemAdapter
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from UFCStats.items import *
from UFCStats.models import *


class UfcStatsPipeline:
    def __init__(self):
        """
        Initializes db connection and sessionmaker. Creates postgres table.
        """
        engine = UFCStats.models.db_connect()
        UFCStats.models.create_table(engine)
        self.Session = sessionmaker(bind=engine)
    
    def process_item(self, item, spider):
        """
        Load scrapy item to the postgres database.
        """
        
        session = self.Session()
        
        if isinstance(item, Event):
            ufc_item = EventTable(**item)
        elif isinstance(item, Fight):
            ufc_item = FightTable(**item)
        elif isinstance(item, Round):
            ufc_item = RoundTable(**item)
        elif isinstance(item, RoundResult):
            ufc_item = RoundResultTable(**item)
        elif isinstance(item, Fighter):
            ufc_item = FighterTable(**item)
        else:
            return item
            
        try:
            session.add(ufc_item)
            session.commit()
        except:
            session.rollback()  #should there be some kind of alert that says which items went wrong?
            raise
        finally:
            session.close()
        
        return item