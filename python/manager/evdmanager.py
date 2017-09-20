from pyqtgraph.Qt import QtCore
import datatypes
from ROOT import larcv
from ROOT import TFile
import ROOT

from processor import processor



class evd_manager_base(QtCore.QObject):

    eventChanged = QtCore.pyqtSignal()

    """docstring for lariat_manager"""

    def __init__(self, _file=None):
        super(evd_manager_base, self).__init__(_file)
        manager.__init__(self, _file)
        QtCore.QObject.__init__(self)

        # For the larcv manager, using the IOManager to get at the data
        self._driver =  larcv.ProcessDriver('ProcessDriver')
        self._io_manager = self._driver.io()

        # Using a processor class to keep track of what is getting drawn
        self._processor = processor()

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

        print self._driver
        self._driver.initialize()

        for x in xrange(larcv.kProductUnknown):    
            print 'Data type', larcv.ProductName(x), 'producers:',    
            for name in self._io_manager.producer_list(x):        
                print name,    
            print

    # This function will return all producers for the given product
    def getProducers(self, product_type):
        if self._io_manager is not None:
            return self._io_manager.producer_list(product_type)

    # This function returns the list of products that can be drawn:
    def getDrawableProducts(self):
        return self._drawableItems.getDict()

    # override the run,event,subrun functions:
    def run(self):
        if self._driver is None:
            return 0
        return self._driver.event_id().run()

    def event(self):
        if self._driver is None:
            return 0
        return self._driver.event_id().event()

    def subrun(self):
        if self._driver is None:
            return 0
        return self._driver.event_id().subRun()

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
            self._io_manager.process_event(self.entry() + 1)
            self.eventChanged.emit()
        else:
            print "On the last event, can't go to next."

    def prev(self):
        if self.entry != 0:
            self._io_manager.process_event(self.entry() - 1)
            self.eventChanged.emit()
        else:
            print "On the first event, can't go to previous."




class evd_manager_2D(evd_manager_base):

    '''
    Class to handle the 2D specific aspects of viewer
    '''

    def __init__(self, file=None):
        super(evd_manager_2D, self).__init__(file)
        self._drawableItems = datatypes.drawableItems()

    # this function is meant for the first request to draw an object or
    # when the producer changes
    def redrawProduct(self, informal_type, product, view_manager):
        # print "Received request to redraw ", product, " by ",producer
        # First, determine if there is a drawing process for this product:
        if product is None:
            if informal_type in self._drawnClasses:
                self._drawnClasses[informal_type].clearDrawnObjects(self._view_manager)
                self._drawnClasses.pop(informal_type)
            return
        if informal_type in self._drawnClasses:
            self._drawnClasses[informal_type].setProducer(product.fullName())
            self.processEvent(True)
            self._drawnClasses[informal_type].clearDrawnObjects(self._view_manager)
            self._drawnClasses[informal_type].drawObjects(self._view_manager)
            return

        # Now, draw the new product
        if informal_type in self._drawableItems.getListOfTitles():
            # drawable items contains a reference to the class, so instantiate
            # it
            drawingClass = self._drawableItems.getDict()[informal_type][0]()
            # Special case for clusters, connect it to the signal:
            # if name == 'Cluster':
            #     self.noiseFilterChanged.connect(
            #         drawingClass.setParamsDrawing)
            #     drawingClass.setParamsDrawing(self._drawParams)
            # if name == 'Match':
            #     self.noiseFilterChanged.connect(
            #         drawingClass.setParamsDrawing)
            #     drawingClass.setParamsDrawing(self._drawParams)
            if informal_type == "RawDigit":
                self.noiseFilterChanged.connect(
                    drawingClass.runNoiseFilter)

            drawingClass.setProducer(product.fullName())
            self._processer.add_process(product, drawingClass._process)
            self._drawnClasses.update({informal_type: drawingClass})
            # Need to process the event
            self.processEvent(True)
            drawingClass.drawObjects(self._view_manager)

    def clearAll(self):
        for recoProduct in self._drawnClasses:
            self._drawnClasses[recoProduct].clearDrawnObjects(
                self._view_manager)
        # self.clearTruth()

    def drawFresh(self):
        # # wires are special:
        if self._drawWires:
          self._view_manager.drawPlanes(self)
        self.clearAll()
        # Draw objects in a specific order defined by drawableItems
        order = self._drawableItems.getListOfTitles()
        # self.drawTruth()
        for item in order:
            if item in self._drawnClasses:
                self._drawnClasses[item].drawObjects(self._view_manager)

    def getAutoRange(self, plane):
        # This gets the max bounds
        xRangeMax, yRangeMax = super(evd_manager_2D, self).getAutoRange(plane)
        xRange = [999,-999]
        yRange = [99999,-99999]
        for process in self._drawnClasses:
            x, y = self._drawnClasses[process].getAutoRange(plane)
            # Check against all four of the parameters:
            if x is not None:
                if x[0] < xRange[0]:
                    xRange[0] = x[0]
                if x[1] > xRange[1]:
                    xRange[1] = x[1]
            if y is not None:
                if y[0] < yRange[0]:
                    yRange[0] = y[0]
                if y[1] > yRange[1]:
                    yRange[1] = y[1]

        # Pad the ranges by 1 cm to accommodate
        padding = 5
        xRange[0] = max(xRangeMax[0], xRange[0] - padding/self._geom.wire2cm())
        xRange[1] = min(xRangeMax[1], xRange[1] + padding/self._geom.wire2cm())
        yRange[0] = max(yRangeMax[0], yRange[0] - padding/self._geom.time2cm())
        yRange[1] = min(yRangeMax[1], yRange[1] + padding/self._geom.time2cm())
        return xRange, yRange

    # handle all the wire stuff:
    def toggleWires(self, product, stage=None):
        # Now, either add the drawing process or remove it:

        if stage is None:
            stage = 'all'

        if product == 'wire':
            if 'recob::Wire' not in self._keyTable[stage]:
                print "No wire data available to draw"
                self._drawWires = False
                return
            self._drawWires = True
            self._wireDrawer = datatypes.recoWire(self._geom)
            self._wireDrawer.setProducer(self._keyTable[stage]['recob::Wire'][0].fullName())
            self._processer.add_process("recob::Wire",self._wireDrawer._process)
            self.processEvent(True)

        elif product == 'rawdigit':
            if 'raw::RawDigit' not in self._keyTable[stage]:
                print "No raw digit data available to draw"
                self._drawWires = False
                return
            self._drawWires = True
            self._wireDrawer = datatypes.rawDigit(self._geom)
            self._wireDrawer.setProducer(self._keyTable[stage]['raw::RawDigit'][0].fullName())
            self._processer.add_process("raw::RawDigit", self._wireDrawer._process)
            self._wireDrawer.toggleNoiseFilter(self.filterNoise)

            self.processEvent(True)
        else:
            if 'raw::RawDigit' in self._processer._ana_units.keys():
                self._processer.remove_process('raw::RawDigit')
            if 'recob::Wire' in self._processer._ana_units.keys():
                self._processer.remove_process('recob::Wire')
            self._wireDrawer = None
            self._drawWires = False

    def toggleNoiseFilter(self, filterBool):
        self.filterNoise = filterBool
        if 'raw::RawDigit' in self._processer._ana_units.keys():
            self._wireDrawer.toggleNoiseFilter(self.filterNoise)
            # Rerun the event just for the raw digits:
            self.processEvent(force=True)
            self.drawFresh()

    def getPlane(self, plane):
        if self._drawWires:
            return self._wireDrawer.getPlane(plane)

    def hasWireData(self):
        if self._drawWires:
            return True
        else:
            return False

    def drawHitsOnWire(self, plane, wire):
        if not 'Hit' in self._drawnClasses:
            return
        else:
            # Get the hits:
            hits = self._drawnClasses['Hit'].getHitsOnWire(plane, wire)
            self._view_manager.drawHitsOnPlot(hits)

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
                self._drawnClasses[name].drawObjects(self._view_manager)
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
                drawingClass.drawObjects(self._view_manager)

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
                    self._drawnClasses[item].drawObjects(self._view_manager)

        def toggleMCCosmic(self, toggleBool):
            self.showMCCosmic = toggleBool
            order=self._drawableItems.getListOfTitles()
            for item in order:
                if item == "MCTrack":
                    if item in self._drawnClasses:
                        self._drawnClasses[item].toggleMCCosmic(toggleBool)
                        self._drawnClasses[item].clearDrawnObjects(self._view_manager)
                        self.processEvent(True)
                        self._drawnClasses[item].drawObjects(self._view_manager)
            #self.drawFresh()

except:
    pass
