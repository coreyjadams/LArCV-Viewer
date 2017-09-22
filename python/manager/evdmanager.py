from pyqtgraph.Qt import QtCore
import datatypes
from ROOT import larcv
from ROOT import TFile
import ROOT


class event_meta(object):

    def __init__(self):
        super(event_meta, self).__init__()
        self._image_metas = dict()
    
    def n_views(self):
        return max(len(self._image_metas), 1)

    def refresh(self, larcv_event_image2d):

        for image2d in larcv_event_image2d.Image2DArray():
            _meta = image2d.meta()
            self._image_metas[_meta.plane()] = _meta

    def meta(self, plane):
        return self._image_metas[plane]

    def row_to_wire(self, row, plane):
        return self._image_metas[plane].pos_x(row)

    def col_to_time(self, col, plane):
        return self._image_metas[plane].pos_y(col)

    def wire_to_col(self, wire, plane):
        return  (wire - self._image_metas[plane].tl().x) / self._image_metas[plane].pixel_width()

    def time_to_row(self, time, plane):
        return  (self._image_metas[plane].tl().y - time) / self._image_metas[plane].pixel_height()
        # return self._image_metas[plane].row(time)

    def range(self, plane):
        if plane in self._image_metas.keys():
            _this_meta = self._image_metas[plane]
            return ((_this_meta.tl().x, _this_meta.tr().x ),
                    (_this_meta.bl().y, _this_meta.tl().y))
        else:
            print "ERROR: plane {} not available.".format(plane)
            return ((-1, 1), (-1, 1))

class evd_manager_base(QtCore.QObject):

    eventChanged = QtCore.pyqtSignal()
    drawFreshRequested = QtCore.pyqtSignal()
    metaRefreshed = QtCore.pyqtSignal(event_meta)

    """docstring for lariat_manager"""

    def __init__(self, config, _file=None):
        super(evd_manager_base, self).__init__()
        QtCore.QObject.__init__(self)


        # For the larcv manager, using the IOManager to get at the data
        self._driver =  larcv.ProcessDriver('ProcessDriver')
        self._driver.configure(config)
        self._io_manager = self._driver.io()

        # Meta keeps track of information about number of planes, visible
        # regions, etc.:
        self._meta = event_meta()


        # Drawn classes is a list of things getting drawn, as well.
        self._drawnClasses = dict()

        self._keyTable = dict()


        if _file != None:
            flist=ROOT.std.vector('std::string')()
            if type(_file) is list:
                for f in _file: flist.push_back(f)
                self._driver.override_input_file(flist)
            else:
                flist.push_back(_file)
                self._driver.override_input_file(flist)

        self._driver.initialize()

        self._data_product_rmap = dict()

        for x in xrange(larcv.kProductUnknown):    
            self._data_product_rmap.update({larcv.ProductName(x)  : x })
            # print larcv.ProductName(x), ": \r"
            # for val in self._io_manager.producer_list(x):
            #     print val + " \r"
            # print

        self.refresh_meta()


    def refresh_meta(self):
        # Read in any of the image2d products if none is specified.
        # Use it's meta info to build up the meta for the viewer
        _id = self._data_product_rmap['image2d']
        _producer = self._io_manager.producer_list(_id).front()
        _event_image2d = self._io_manager.get_data(_id, _producer)
        
        self._meta.refresh(_event_image2d)

    def meta(self):
        return self._meta

    # This function will return all producers for the given product
    def getProducers(self, product):
        _id = self._data_product_rmap[product]
        if self._io_manager is not None:
            return self._io_manager.producer_list(_id)

    # This function returns the list of products that can be drawn:
    def getDrawableProducts(self):
        return self._drawableItems.getDict()

    # override the run,event,subrun functions:
    def run(self):
        if self._io_manager is None:
            return 0
        return self._io_manager.event_id().run()

    def event(self):
        if self._io_manager is None:
            return 0
        return self._io_manager.event_id().event()

    def subrun(self):
        if self._io_manager is None:
            return 0
        return self._io_manager.event_id().subrun()

    # def internalEvent(self):
    def entry(self):
        if self._io_manager is not None:
            return self._io_manager.current_entry()
        else:
            return -1

    def n_entries(self):
        if self._io_manager is not None:
            return self._io_manager.get_n_entries()
        else:
            return 0

    # override the functions from manager as needed here
    def next(self):
        if self.entry() + 1 < self.n_entries():
            self._driver.batch_process(self.entry() + 1, 1)
            self.eventChanged.emit()
        else:
            print "On the last event, can't go to next."

    def prev(self):
        if self.entry != 0:
            self._driver.batch_process(self.entry() - 1, 1)
            self.eventChanged.emit()
        else:
            print "On the first event, can't go to previous."

    def go_to_entry(self, entry):
        if entry >= 0 and entry < self.n_entries():
            self._driver.batch_process(entry, 1)
            self.eventChanged.emit()
        else:
            print "Can't go to entry {}, entry is out of range.".format(entry)

    def range(self, plane):
        # To get the range, we ask for the image meta and use it:
        return self._meta.range(plane)

    def n_views(self):
        return self._meta.n_views()

class evd_manager_2D(evd_manager_base):

    '''
    Class to handle the 2D specific aspects of viewer
    '''

    def __init__(self, config, _file=None):
        super(evd_manager_2D, self).__init__(config, _file)
        self._drawableItems = datatypes.drawableItems()

    # this function is meant for the first request to draw an object or
    # when the producer changes
    def redrawProduct(self, product, producer, view_manager):
        
        # print "Received request to redraw ", product, " by ",producer
        # First, determine if there is a drawing process for this product:  
        
        if producer is None:
            if product in self._drawnClasses:
                self._drawnClasses[product].clearDrawnObjects(view_manager)
                self._drawnClasses.pop(product)
            return
        if product in self._drawnClasses:
            self._drawnClasses[product].setProducer(producer)
            self._drawnClasses[product].clearDrawnObjects(view_manager)
            self._drawnClasses[product].drawObjects(view_manager, self._io_manager, self.meta())
            return

        # Now, draw the new product
        if product in self._drawableItems.getListOfTitles():
            # drawable items contains a reference to the class, so
            # instantiate it
            drawingClass=self._drawableItems.getDict()[product][0]()

            drawingClass.setProducer(producer)
            self._drawnClasses.update({product: drawingClass})

            # Need to process the event
            drawingClass.drawObjects(view_manager, self._io_manager, self.meta())


    def clearAll(self, view_manager):
        for recoProduct in self._drawnClasses:
            self._drawnClasses[recoProduct].clearDrawnObjects(view_manager)
        # self.clearTruth()

    def drawFresh(self, view_manager):

        self.clearAll(view_manager)
        # Draw objects in a specific order defined by drawableItems
        order = self._drawableItems.getListOfTitles()
        # self.drawTruth()
        for item in order:
            if item in self._drawnClasses:
                self._drawnClasses[item].drawObjects(view_manager, self._io_manager, self.meta())



    def getPlane(self, plane):
        if self._drawWires:
            return self._wireDrawer.getPlane(plane)

try:
    import pyqtgraph.opengl as gl

    class evd_manager_3D(evd_manager_base):

        """This class handles file I/O and drawing for 3D viewer"""

        showMCCosmic = True

        def __init__(self, file=None):
            super(evd_manager_3D, self).__init__(file)
            self._drawableItems = datatypes.drawableItems3D()

        def getAutoRange(self):
            pass

        # this function is meant for the first request to draw an object or
        # when the producer changes
        def redrawProduct(self, name, product, producer, view_manager, stage = None):
            # print "Received request to redraw ", product, " by ",producer, " with name ", name
            # First, determine if there is a drawing process for this product:  
            if stage is None:
                stage = 'all'         
            if producer is None:
                if name in self._drawnClasses:
                    self._drawnClasses[name].clearDrawnObjects(self._view_manager)
                    self._drawnClasses.pop(name)
                return
            if name in self._drawnClasses:
                self._drawnClasses[name].setProducer(producer)
                self.processEvent(True)
                self._drawnClasses[name].clearDrawnObjects(self._view_manager)
                self._drawnClasses[name].drawObjects(self._view_manager, self.meta())
                return


            # Now, draw the new product
            if name in self._drawableItems.getListOfTitles():
                # drawable items contains a reference to the class, so
                # instantiate it
                drawingClass=self._drawableItems.getDict()[name][0]()
                # Special case for clusters, connect it to the signal:
                # if name is 'PFParticle':
                    # self.noiseFilterChanged.connect(
                    #     drawingClass.setParamsDrawing)
                    # drawingClass.setParamsDrawing(self._drawParams)
                # if name == 'Match':
                #     self.noiseFilterChanged.connect(
                #         drawingClass.setParamsDrawing)
                #     drawingClass.setParamsDrawing(self._drawParams)

                drawingClass.setProducer(producer)
                self._processer.add_process(product, drawingClass._process)
                self._drawnClasses.update({name: drawingClass})
                if name == "MCTrack":
                    self._drawnClasses[name].toggleMCCosmic(self.showMCCosmic)
                # Need to process the event
                self.processEvent(True)
                drawingClass.drawObjects(self._view_manager, self.meta())

        def clearAll(self):
            for recoProduct in self._drawnClasses:
                self._drawnClasses[recoProduct].clearDrawnObjects(
                    self._view_manager)

        # def toggleParams(self, paramsBool):
        #     self._drawParams=paramsBool
        #     self.noiseFilterChanged.emit(paramsBool)
        #     if 'PFParticle' in self._drawnClasses:
        #         self.drawFresh()

        def drawFresh(self):
            # # wires are special:
            # if self._drawWires:
            #   self._view_manager.drawPlanes(self)
            self.clearAll()
            # Draw objects in a specific order defined by drawableItems
            order=self._drawableItems.getListOfTitles()
            for item in order:
                if item in self._drawnClasses:
                    self._drawnClasses[item].drawObjects(self._view_manager, self.meta())


except:
    pass
