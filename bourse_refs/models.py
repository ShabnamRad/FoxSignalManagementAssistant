from django.db import models


class Stock(models.Model):
    BOURSE = 'bourse'
    FARA_BOURSE = 'fara_bourse'
    STOCK_TYPES = (
        (BOURSE, 'bourse'),
        (FARA_BOURSE, 'fara bourse'),
    )

    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=500)
    CIsin = models.CharField(max_length=20)
    stock_type = models.CharField(
        max_length=20,
        choices=STOCK_TYPES,
    )
    category = models.CharField(max_length=100)

    @property
    def detail_url(self):
        return 'http://www.tsetmc.com/Loader.aspx?ParTree=15131J&i={}'.format(self.id)

    @classmethod
    def get_stock(cls, name):
        return Stock.objects.get(name=name)


class StockHistory(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT)
    date = models.DateField()
    max_price = models.IntegerField()
    min_price = models.IntegerField()
    last_price = models.IntegerField()
    last_deal_price = models.IntegerField()
    first_price = models.IntegerField()
    yesterday_price = models.IntegerField()
    value = models.BigIntegerField()
    volume = models.BigIntegerField()
    count = models.IntegerField()

    num_stocks = models.BigIntegerField(null=True, blank=True)
    base_volume = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['date']


class StockOwnership(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT)
    date = models.DateField()
    owner_id = models.IntegerField()
    owner_name = models.CharField(max_length=100)
    percent = models.FloatField()
    num_stocks = models.BigIntegerField()
    stock_key = models.CharField(max_length=20)

    class Meta:
        unique_together = ('stock', 'date', 'owner_id')


class StockTrades(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT)
    datetime = models.DateTimeField()
    volume = models.PositiveIntegerField()
    price = models.PositiveIntegerField()


class StockInfo(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT)
    datetime = models.DateTimeField()
    last_trade_price = models.PositiveIntegerField()
    last_price = models.PositiveIntegerField()
    first_price = models.PositiveIntegerField()
    yesterday_price = models.PositiveIntegerField()
    max_price = models.PositiveIntegerField()
    min_price = models.PositiveIntegerField()
    trade_count = models.PositiveIntegerField()
    trade_volume = models.BigIntegerField()
    trade_value = models.BigIntegerField()


class BuyAndSellOrder(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT)
    datetime = models.DateTimeField()
    position = models.IntegerField()
    buy_count = models.IntegerField()
    buy_volume = models.BigIntegerField()
    buy_price = models.IntegerField()
    sell_price = models.IntegerField()
    sell_volume = models.BigIntegerField()
    sell_count = models.IntegerField()


class NaturalLegalPersonsTrade(models.Model):
    SELL = 'sell'
    BUY = 'buy'
    TRADE_TYPES = (
        (SELL, 'sell'),
        (BUY, 'buy'),
    )
    NATURAL_PERSON = 'natural'
    LEGAL_PERSON = 'legal'
    PERSON_TYPES = (
        (NATURAL_PERSON, 'natural person'),
        (LEGAL_PERSON, 'legal person'),
    )
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT)
    date = models.DateField()
    type = models.CharField(max_length=10, choices=TRADE_TYPES)
    person_type = models.CharField(max_length=10, choices=PERSON_TYPES)

    count = models.IntegerField()
    volume = models.BigIntegerField()
    value = models.BigIntegerField()
    average_price = models.FloatField()
