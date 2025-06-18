import csv
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()

class Tender(Base):
    __tablename__ = 'tenders'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    pub_date = Column(String, nullable=True)
    submission_deadline = Column(String, nullable=True)
    eligibility = Column(Text, nullable=True)
    contact = Column(String, nullable=True)
    link = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    country = Column(String, nullable=True)
    issuer = Column(String, nullable=True)

class SqlitePipeline:
    def __init__(self, sqlite_file):
        self.sqlite_file = sqlite_file

    @classmethod
    def from_crawler(cls, crawler):
        return cls(sqlite_file=crawler.settings.get('SQLITE_FILE'))

    def open_spider(self, spider):
        # Avoid deleting database to prevent PermissionError
        logger.info(f"Using existing database: {self.sqlite_file}")
        self.engine = create_engine(f'sqlite:///{self.sqlite_file}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"Initialized SQLite database: {self.sqlite_file}")

    def process_item(self, item, spider):
        try:
            session = self.Session()
            tender = Tender(
                title=item.get('title'),
                description=item.get('description'),
                pub_date=item.get('pub_date'),
                submission_deadline=item.get('submission_deadline'),
                eligibility=item.get('eligibility'),
                contact=item.get('contact'),
                link=item.get('link'),
                source_url=item.get('source_url'),
                country=item.get('country'),
                issuer=item.get('issuer')
            )
            session.add(tender)
            session.commit()
            logger.debug(f"Saved item to database: {item.get('title')}")
            session.close()
            return item
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving item to database: {e}")
            session.close()
            raise

class CsvPipeline:
    def open_spider(self, spider):
        self.file = open('tenders_output.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.file, fieldnames=[
            'title', 'description', 'pub_date', 'submission_deadline', 'eligibility',
            'contact', 'link', 'source_url', 'country', 'issuer'
        ])
        self.writer.writeheader()
        logger.info("Initialized CSV file: tenders_output.csv")

    def close_spider(self, spider):
        self.file.close()
        logger.info("Closed CSV file")

    def process_item(self, item, spider):
        try:
            self.writer.writerow({k: item.get(k, '') for k in self.writer.fieldnames})
            logger.debug(f"Saved item to CSV: {item.get('title')}")
            return item
        except Exception as e:
            logger.error(f"Error saving item to CSV: {e}")
            raise

class TextPipeline:
    def open_spider(self, spider):
        self.file = open('tenders_output.txt', 'w', encoding='utf-8')
        logger.info("Initialized text file: tenders_output.txt")

    def close_spider(self, spider):
        self.file.close()
        logger.info("Closed text file")

    def process_item(self, item, spider):
        try:
            self.file.write(f"Title: {item.get('title', '')}\n")
            self.file.write(f"Issuer: {item.get('issuer', '')}\n")
            self.file.write(f"Country: {item.get('country', '')}\n")
            self.file.write(f"Description: {item.get('description', '')}\n")
            self.file.write(f"Publication Date: {item.get('pub_date', '')}\n")
            self.file.write(f"Submission Deadline: {item.get('submission_deadline', '')}\n")
            self.file.write(f"Eligibility: {item.get('eligibility', '')}\n")
            self.file.write(f"Contact: {item.get('contact', '')}\n")
            self.file.write(f"Link: {item.get('link', '')}\n")
            self.file.write(f"Source URL: {item.get('source_url', '')}\n")
            self.file.write("-" * 80 + "\n")
            logger.debug(f"Saved item to text file: {item.get('title')}")
            return item
        except Exception as e:
            logger.error(f"Error saving item to text file: {e}")
            raise