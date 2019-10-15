import random
from unittest import TestCase

from EmexCatalogSpider.dumper import CSVDumper, DescCarRepr


class TestCSVDumper(TestCase):
    test_dataset = [
        DescCarRepr("a", 1),
        DescCarRepr("b", 2),
        DescCarRepr("c", 3),
        DescCarRepr("d", 4),
        DescCarRepr("e", 5),
        DescCarRepr("f", 6),
        DescCarRepr("g", 7),
        DescCarRepr("h", 8),
        DescCarRepr("i", 9),
        DescCarRepr("j", 10),
    ]

    def test_push_desc_len(self):
        random.shuffle(self.test_dataset)
        desc_queue_size = 5
        dumper = CSVDumper(desc_queue_size)

        def p(e):
            dumper.push(e)
            return e

        self.test_dataset = list(map(p, self.test_dataset))

        self.assertEqual(len(dumper.top_queue), desc_queue_size)

    def test_push_desc_content(self):
        random.shuffle(self.test_dataset)
        desc_queue_size = 5
        dumper = CSVDumper(desc_queue_size)

        def p(e):
            dumper.push(e)
            return e

        self.test_dataset = list(map(p, self.test_dataset))

        test_list = [
            DescCarRepr("j", 10),
            DescCarRepr("i", 9),
            DescCarRepr("h", 8),
            DescCarRepr("g", 7),
            DescCarRepr("f", 6),
        ]
        actual_list = dumper.top_queue.data
        self.assertListEqual(list(map(str, test_list)), list(map(str, actual_list)))

    def test_push_asc_len(self):
        random.shuffle(self.test_dataset)
        desc_queue_size = 5
        dumper = CSVDumper(desc_queue_size)

        def p(e):
            dumper.push(e)
            return e

        self.test_dataset = list(map(p, self.test_dataset))
        self.assertEqual(len(dumper.least_queue), desc_queue_size)

    def test_push_asc_content(self):
        random.shuffle(self.test_dataset)
        desc_queue_size = 5
        dumper = CSVDumper(desc_queue_size)

        def p(e):
            dumper.push(e)
            return e

        self.test_dataset = list(map(p, self.test_dataset))

        test_list = [
            DescCarRepr("a", 1),
            DescCarRepr("b", 2),
            DescCarRepr("c", 3),
            DescCarRepr("d", 4),
            DescCarRepr("e", 5),
        ]
        actual_list = dumper.least_queue.data
        self.assertListEqual(list(map(str, test_list)), list(map(str, actual_list)))
