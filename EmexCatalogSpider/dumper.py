import csv

from EmexCatalogSpider.substitution_queue import SubstitutionQueue


class CarReprDataClass:
    __slots__ = ("car_name", "parts_count")

    def __init__(self, car_name: str, parts_count: int):
        super().__init__()
        self.car_name = car_name
        self.parts_count = parts_count

    def __str__(self):
        return "{}:{}".format(self.car_name, self.parts_count)


class DescCarRepr(CarReprDataClass):
    def __init__(self, car_name: str, parts_count: int):
        super().__init__(car_name, parts_count)

    def __lt__(self, other):
        return self.parts_count > other.parts_count

    def __gt__(self, other):
        return self.parts_count < other.parts_count


class AscCarRepr(CarReprDataClass):
    def __init__(self, car_name: str, parts_count: int):
        super().__init__(car_name, parts_count)

    def __lt__(self, other):
        return self.parts_count < other.parts_count

    def __gt__(self, other):
        return self.parts_count > other.parts_count


class DataDumper:

    def push(self, *args, **kwargs):
        raise NotImplementedError

    def dump(self, *args, **kwargs):
        raise NotImplementedError


class CSVDumper(DataDumper):
    def __init__(self, size: int):
        super().__init__()
        self.maxsize = size
        self.top_queue = SubstitutionQueue(size)
        self.least_queue = SubstitutionQueue(size)

    def push(self, car_repr: CarReprDataClass):
        l_car_repr = AscCarRepr(car_repr.car_name, car_repr.parts_count)
        t_car_repr = DescCarRepr(car_repr.car_name, car_repr.parts_count)

        self.top_queue.push(t_car_repr)
        self.least_queue.push(l_car_repr)

    def dump(self, top_filepath: str, least_filepath: str):
        with open(top_filepath, 'w', newline='') as csvfile:
            self._file_dump(csvfile, self.top_queue)

        with open(least_filepath, 'w', newline='') as csvfile:
            self._file_dump(csvfile, self.least_queue)

    @staticmethod
    def _file_dump(file, elem_queue):
        fieldnames = ['car_name', 'parts_count']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        while not elem_queue.is_empty():
            elem = elem_queue.pop()
            writer.writerow({"car_name": elem.car_name, "parts_count": elem.parts_count})
