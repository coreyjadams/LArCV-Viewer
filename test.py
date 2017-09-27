from ROOT import larcv
import ROOT

# mode="readOnly"
mode=""

if mode == "readOnly":
    config = "config/default3D.cfg"
else:
    config = "config/voxel.cfg"

# For the larcv manager, using the IOManager to get at the data
driver =  larcv.ProcessDriver('ProcessDriver')
driver.configure(config)
io_manager = driver.io()

_file = "larcv_0051_e.root"

if _file != None:
    flist=ROOT.std.vector('std::string')()
    if type(_file) is list:
        for f in _file: flist.push_back(f)
        driver.override_input_file(flist)
    else:
        flist.push_back(_file)
        driver.override_input_file(flist)

driver.initialize()
driver.batch_process(0, 1)


producers = dict()
for _id in xrange(6):
    print larcv.ProductName(_id), ":"
    for producer in io_manager.producer_list(_id):
        print "  {}".format(producer)


event_voxel3d_1 = io_manager.get_data(5, "simvoxel")
print "Number of voxels by simvoxel: {}".format(event_voxel3d_1.GetVoxelSet().size())

if mode != "readOnly":
    event_voxel3d_2 = io_manager.get_data(5, "simvoxel2")
    print "Number of voxels by simvoxel2: {}".format(event_voxel3d_2.GetVoxelSet().size())

