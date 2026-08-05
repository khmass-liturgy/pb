import unittest

from scripts.fetch_poultry_price import parse_chicken, parse_cow, parse_egg, parse_pig


class PoultryPriceParserTests(unittest.TestCase):
    def test_egg_selects_xl_farm_price_per_10(self):
        html = """
        <table><tr><th>날짜</th><th>산지 XL 30개</th><th>산지 XL 10개</th><th>도매 30개</th><th>도매 10개</th></tr>
        <tr><td>08월 03일</td><td>6,818</td><td>2,273</td><td>7,307</td><td>2,436</td></tr></table>
        """
        self.assertEqual(parse_egg(html)[0]["value"], 2273)

    def test_chicken_selects_live_distribution_large(self):
        html = """
        <table><tr><th>날짜</th><th>생계유통(대)</th><th>위탁생계(중)</th><th>도매</th><th>소매</th></tr>
        <tr><td>08월 04일</td><td>2,000</td><td>1,708</td><td>3,687</td><td>3,600</td></tr></table>
        """
        self.assertEqual(parse_chicken(html)[0]["value"], 2000)

    def test_pig_selects_farm_receipt_average(self):
        html = """
        <table><tr><th>구분</th><th>농가수취 평균</th><th>농가수취 비육돈</th></tr>
        <tr><td>금일 (07월 31일)</td><td>6,388</td><td>539</td></tr></table>
        """
        self.assertEqual(parse_pig(html)[0]["value"], 6388)

    def test_cow_selects_three_requested_farm_price_columns(self):
        html = """
        <table><tr><th>날짜</th><th>암송아지(6~7개월)</th><th>수송아지(6~7개월)</th><th>농가수취가격(600kg)</th><th>평균</th></tr>
        <tr><td>08월 05일</td><td>-</td><td>-</td><td>-</td><td>22,071</td></tr>
        <tr><td>07월 30일</td><td>3,803</td><td>5,103</td><td>7,514</td><td>20,977</td></tr></table>
        """
        rows = parse_cow(html)
        self.assertEqual(rows[0]["female_calf"], None)
        self.assertEqual(rows[1]["farm_receipt_600kg"], 7514)
