import scrapy

class TenderItem(scrapy.Item):
    title = scrapy.Field()
    description = scrapy.Field()
    pub_date = scrapy.Field()
    submission_deadline = scrapy.Field()
    eligibility = scrapy.Field()
    contact = scrapy.Field()
    link = scrapy.Field()
    source_url = scrapy.Field()
    country = scrapy.Field()
    issuer = scrapy.Field()