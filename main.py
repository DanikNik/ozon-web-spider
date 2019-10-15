import re

import logging

from EmexCatalogSpider.dumper import CSVDumper
from EmexCatalogSpider.spider import EmexSpider


def main():
    logging.basicConfig(level=logging.INFO)
    spy = EmexSpider(CSVDumper(20))
    spy.run()


if __name__ == "__main__":
    main()
