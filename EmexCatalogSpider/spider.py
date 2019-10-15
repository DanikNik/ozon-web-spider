import json
import logging
import os
import re

from bs4 import BeautifulSoup
from requests import Session

from EmexCatalogSpider.decorators import retry
from EmexCatalogSpider.dumper import DataDumper, CarReprDataClass
from EmexCatalogSpider.mixins import ProxyRotateMixin, UserAgentRotateMixin, RandomSleepMixin


class WebSpider:
    def run(self):
        raise NotImplementedError


class EmexSpider(WebSpider, ProxyRotateMixin, UserAgentRotateMixin, RandomSleepMixin):
    def __init__(self, dumper: DataDumper):
        ProxyRotateMixin.__init__(self)
        UserAgentRotateMixin.__init__(self)
        RandomSleepMixin.__init__(self)

        self.root_url = "https://emex.ru/catalogs/original"
        self.get_catalog_list_url = "https://emex.ru/Catalog/Laximo/GetCatalogList"
        self.get_wizard2_url = "https://emex.ru/Catalog/Laximo/GetWizard2"
        self.get_vehicle_by_wizard2_url = "https://emex.ru/Catalog/Laximo/GetVehicleByWizard2"
        self.get_vehicle_by_id_url = "https://emex.ru/Catalog/Laximo/GetVehicleById"
        self.get_detail_groups_url = "https://emex.ru/Catalog/Laximo/GetDetailGroups"
        self.get_group_units_url = "https://emex.ru/Catalog/Laximo/GetGroupUnits"

        self.dumper = dumper
        self.session = Session()
        self.context = dict()
        logging.info("Emex spider initialized")

    @retry(3)
    def get_request_verification_token(self):
        result = self.session.get(self.root_url)
        if result.status_code != 200:
            raise ValueError("result_status_code", result.status_code)
        soup = BeautifulSoup(result.text, features="lxml")
        request_verification_token = soup.find("input", attrs={"name": "__RequestVerificationToken"})["value"]
        self.context["request_verification_token"] = request_verification_token
        logging.debug("Got request verification token")
        self.sleep()

    @retry(5)
    def get_catalog_list(self):
        self.new_identity()

        catalog_list = self.session.post(self.get_catalog_list_url, data={
            "__RequestVerificationToken": self.context["request_verification_token"]
        })
        if catalog_list.status_code != 200:
            raise ValueError("catalog_list_status_code", catalog_list.status_code)
        self.context["catalog_list"] = catalog_list.text.strip()
        logging.debug("Got catalog list")
        self.sleep()

    @retry(5)
    def new_identity(self):
        self.session.close()
        self.session = Session()
        self.session.headers.update(self.rotate_ua())
        # proxy = self.rotate_proxy()
        # self.session.proxies.update({"http": proxy, "https": proxy})
        self.get_request_verification_token()

    @retry(5)
    def crawl_through_brand(self):
        brand = self.context["current_brand"]
        if not brand["supportwizard2"]:
            return

        logging.info("Parsing brand: {}".format(brand["name"]))

        catalog_id = brand["catalogid"]
        self.context["catalog_id"] = catalog_id
        self.new_identity()
        wizard2_options_response = self.session.post(self.get_wizard2_url, data={
            "__RequestVerificationToken": self.context["request_verification_token"],
            "catalogId": catalog_id
        })
        if wizard2_options_response.status_code != 200:
            raise ValueError("wizard2_status_code", wizard2_options_response.status_code)
        # get model list via Wizard2
        models_list = json.loads(wizard2_options_response.text.strip())[0]["Options"]
        self.sleep()

        for model in models_list:
            self.context["current_model"] = model
            self.crawl_through_model_modifications()

    @retry(5)
    def crawl_through_model_modifications(self):
        model = self.context["current_model"]
        logging.info("Parsing model: {}".format(model["Value"]))
        ssd = model["WizardId"]
        self.new_identity()
        get_cars_by_wizard_options = self.session.post(self.get_vehicle_by_wizard2_url, data={
            "__RequestVerificationToken": self.context["request_verification_token"],
            "catalogId": self.context["catalog_id"],
            "ssd": ssd
        })
        if get_cars_by_wizard_options.status_code != 200:
            raise ValueError("get_cars_by_wizard_status_code", get_cars_by_wizard_options.status_code)
        self.sleep()
        cars_list = json.loads(get_cars_by_wizard_options.content)

        for car in cars_list:
            self.context["current_parts_counter"] = 0
            self.context["current_car_modification"] = car
            car_name = '|'.join([car["model"], car["brand"], car["name"]])
            logging.info("Parsing car modification: {}".format(car_name))
            self.crawl_through_modification_parts()
            self.dumper.push(CarReprDataClass(car_name, self.context["current_parts_counter"]))

    @retry(5)
    def crawl_through_modification_parts(self):
        car = self.context["current_car_modification"]
        ssd = car["ssd"]
        vehicle_id = car["vehicleid"]
        catalog_id = self.context["catalog_id"]
        self.new_identity()
        parts_groups_tree_response = self.session.post(self.get_detail_groups_url, data={
            "catalogId": catalog_id,
            "vehicleId": vehicle_id,
            "ssd": ssd,
            "__RequestVerificationToken": self.context["request_verification_token"]
        })
        if parts_groups_tree_response.status_code != 200:
            raise ValueError("parts_group_tree_status_code", parts_groups_tree_response.status_code)

        self.sleep()
        # this regex matches fields in json which have DetailGroups = [], which means that they are leaves in tree
        groupid_regex = re.compile(r'"DetailGroups":\s*\[\],\s*.+?\s*,\s*"quickgroupid":\s*"([0-9]+)"')

        group_ids = groupid_regex.findall(parts_groups_tree_response.text)
        for gid in group_ids:
            self.context["gid"] = gid
            self.crawl_through_parts_group()

    @retry(2)
    def crawl_through_parts_group(self):
        gid = self.context["gid"]
        car = self.context["current_car_modification"]
        ssd = car["ssd"]
        vehicle_id = car["vehicleid"]
        catalog_id = self.context["catalog_id"]

        self.new_identity()
        group_units = self.session.post(self.get_group_units_url, data={
            "catalogId": catalog_id,
            "vehicleId": vehicle_id,
            "ssd": ssd,
            "groupId": gid,
            "__RequestVerificationToken": self.context["request_verification_token"]
        })
        if group_units.status_code != 200:
            raise ValueError("groups_units_status_code", group_units.status_code)
        self.sleep()

        units = json.loads(group_units.text)
        group_units_count = 0
        for i in units:
            group_units_count += len(i["detailsMatch"])

        logging.debug("{}: {}".format(gid, group_units_count))
        self.context["current_parts_counter"] += group_units_count

    def run(self):
        try:
            self.get_catalog_list()
            brands_list = json.loads(self.context["catalog_list"])["brands"]
            # c = 0
            for brand in brands_list:
                # c += 1
                self.context["current_brand"] = brand
                self.crawl_through_brand()
                # if c == 2:
                #     break
            self.dumper.dump(
                os.getenv("TOP_CSV_PATH", "output/top.csv"),
                os.getenv("LEAST_CSV_PATH", "output/least20.csv")
            )
        except KeyboardInterrupt:
            logging.info("Graceful shutdown...")
        finally:
            self.session.close()
