from image2d import image2d
from pixel2d import pixel2d

# This is the class that maintains the list of drawable items.
# If your class isn't here, it can't be drawn
import collections


class drawableItems(object):

    """This class exists to enumerate the drawableItems"""
    # If you make a new drawing class, add it here

    def __init__(self):
        super(drawableItems, self).__init__()
        # items are stored as pointers to the classes (not instances)
        self._drawableClasses = collections.OrderedDict()
        self._drawableClasses.update({'Image2D': [image2d, 'image2d']})
        self._drawableClasses.update({'Pixel2D': [pixel2d, 'pixel2d']})

    def getListOfTitles(self):
        return self._drawableClasses.keys()

    def getListOfItems(self):
        return zip(*self._drawableClasses.values())[1]

    def getDict(self):
        return self._drawableClasses


try:
    import pyqtgraph.opengl as gl
    class drawableItems3D(object):

        """This class exists to enumerate the drawableItems in 3D"""
        # If you make a new drawing class, add it here

        def __init__(self):
            super(drawableItems3D, self).__init__()
            # items are stored as pointers to the classes (not instances)
            self._drawableClasses = collections.OrderedDict()
            # self._drawableClasses.update({'Spacepoints': [spacepoint.spacepoint3D,"recob::SpacePoint"]})
            # self._drawableClasses.update({'PFParticle': [pfpart.pfpart3D,"recob::PFParticle"]})
            # self._drawableClasses.update({'Seed': [seed.seed3D,"recob::Seed"]})
            # self._drawableClasses.update({'Vertex': [vertex.vertex3D,"recob::Vertex"]})
            # self._drawableClasses.update({'Shower': [shower.shower3D,"recob::Shower"]})
            # self._drawableClasses.update({'Track': [track.track3D,"recob::Track"]})
            # self._drawableClasses.update({'Opflash': [opflash.opflash3D,"recob::OpFlash"]})
            # self._drawableClasses.update({'MCTrack': [mctrack.mctrack3D,"sim::MCTrack"]})
            # self._drawableClasses.update({'MCShower': [mcshower.mcshower3D,"sim::MCShower"]})
            # self._drawableClasses.update({'Simch': [simch.simch3D,"sim::SimChannel"]})

        def getListOfTitles(self):
            return self._drawableClasses.keys()

        def getListOfItems(self):
            return zip(*self._drawableClasses.values())[1]

        def getDict(self):
            return self._drawableClasses



except:
    pass

