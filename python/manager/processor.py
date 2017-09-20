


class processor(object):
    """
    This class handles instances of things from datatypes, such as Image2D,
    and keeps track of everything being run in the event display.  Many functions here
    require IOManager as input.

    This is meant to be the only reference to processing classes, so that when
    something is 'undrawn' it goes away entirely.
    """
    def __init__(self):
        super(processor, self).__init__()
        # Storing ana units as a map:
        # self._ana_units[data product] -> instance of ana_unit
        self._ana_units = dict()
        pass

    def process_event(self, io_manager):
        # print "Running ... "
        for key in self._ana_units:
            # print "Processing " + key
            self._ana_units[key].analyze(io_manager)

    def add_process(self, data_product, ana_unit):
        if data_product in self._ana_units:
            self._ana_units.pop(data_product)
        self._ana_units.update({data_product : ana_unit})
        return

    def remove_process(self, data_product, ana_unit=None):
        if data_product in self._ana_units:
            self._ana_units.pop(data_product)
        return

    def get_process(self, data_product):
        if data_product in self._ana_units:
            return self._ana_units[data_product]
        else:
            return None

    def reset():
        self._ana_units = dict()