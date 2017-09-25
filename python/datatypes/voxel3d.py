from database import recoBase
from pyqtgraph.Qt import QtGui, QtCore
import numpy
try:
    import pyqtgraph.opengl as gl
except:
    print "Error, must have open gl to use this viewer."
    exit(-1)

class voxel3d(recoBase):

    """docstring for voxel3d"""

    def __init__(self):
        super(voxel3d, self).__init__()
        self._productName = 'voxel3d'
        self._product_id = 5
        self._glPointsCollection = None

    # this is the function that actually draws the cluster.
    def drawObjects(self, view_manager, io_manager, meta):

        #Get the list of voxel3d sets:
        event_voxel3d = io_manager.get_data(self._product_id, str(self._producerName))

        voxels = event_voxel3d.GetVoxelSet()
        meta = event_voxel3d.GetVoxelMeta()

        print meta.NumVoxelX()
        print voxels.size()

        # using spheres at the moment:
        self._points = numpy.ndarray((voxels.size(), 3))
        self._color = numpy.ndarray((voxels.size(), 4))
        self._values = numpy.ndarray((voxels.size()))

        # # This section draws voxels onto the environment:
        i = 0
        for voxel in voxels:
            _pos = meta.Position(voxel.ID())
            self._points[i][0] = _pos[0] - meta.MinX()
            self._points[i][1] = _pos[1] - meta.MinY()
            self._points[i][2] = _pos[2] - meta.MinZ()
            self._values[i] = voxel.Value()
            i += 1
            # print voxel.Value()

        self.setColors(view_manager.getLookupTable(), view_manager.getLevels())
        self.redrawPoints(view_manager)

    def redrawPoints(self, view_manager):
        if self._glPointsCollection is not None:
            view_manager.getView().removeItem(self._glPointsCollection)

        self._glPointsCollection = gl.GLScatterPlotItem(pos=self._points,
            size=25, color=self._color)

        view_manager.getView().addItem(self._glPointsCollection)

    def setColors(self, _lookupTable, levels):
        _min = levels[0]
        _max = levels[1]

        for i in xrange(len(self._values)):
            if self._values[i] >= _max:
                # print "Max " + str(self._values[i])
                self._color[i] = (0,0,0,0)
            elif self._values[i] <= _min:
                # print "Min "  + str(self._values[i])
                self._color[i] = (0,0,0,0)
            else:
                index = 255*(self._values[i] - _min) / (_max - _min)
                self._color[i] = _lookupTable[int(index)]

    def clearDrawnObjects(self, view_manager):
        if self._glPointsCollection is not None:
            view_manager.getView().removeItem(self._glPointsCollection)
        self._glPointsCollection = None

    def refresh(self, view_manager):
        print "Refreshing"
        self.setColors(view_manager.getLookupTable(), view_manager.getLevels())
        self.redrawPoints(view_manager)