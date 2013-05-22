import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pylab
import scipy.signal as spsig
import scipy.stats as sps
import math
import struct
import re

def showIm(*args):
    if len(args) == 0:
        print "showIm( matrix, range, zoom, label, colormap, colorbar )"
        print "  matrix is string. It should be the name of a 2D array."
        print "  range is a two element tuple.  It specifies the values that "
        print "    map to the min and max colormap values.  Passing a value "
        print "    of 'auto' (default) sets range=[min,max].  'auto2' sets "
        print "    range=[mean-2*stdev, mean+2*stdev].  'auto3' sets "
        print "    range=[p1-(p2-p1)/8, p2+(p2-p1)/8], where p1 is the 10th "
        print "    percientile value of the sorted matix samples, and p2 is "
        print "    the 90th percentile value."
        print "  zoom specifies the number of matrix smples per screen pixel. "
        print "    It will be rounded to an integer, or 1 divided by an "
        print "    integer.  A value of 'same' or 'auto' (default) causes the "
        print "    zoom value to be chosen automatically to fit the image into "
        print "    the current axes.  A value of 'full' fills the axis region "
        print "    (leaving no room for labels)."
        print "  If label (optional, default = 1, unless zoom = 'full') is "
        print "    non-zero, the range of values that are mapped into the "
        print "    colormap and the dimensions (size) of the matrix and zoom "
        print "    factor are printed below the image.  If label is a string, "
        print "    it is used as a title."
        print "  colormap must contain the string 'auto' (grey colormap with " 
        print "    size = matrix.max() - matrix.min() will be used), "
        print "    or a string that is the name of a colormap variable "
        print "  colorbar is a boolean that specifies whether or not a "
        print "    colorbar is displayed"
    if len(args) > 0:   # matrix entered
        matrix = args[0]
        # defaults for all other values in case they weren't entered
        imRange = ( np.amin(matrix), np.amax(matrix) )
        zoom = 1
        label = 1
        colorbar = False
        colormap = cm.Greys_r
    if len(args) > 1:   # range entered
        if isinstance(args[1], basestring):
            if args[1] is "auto":
                imRange = ( np.amin(matrix), np.amax(matrix) )
            elif args[1] is "auto2":
                imRange = ( matrix.mean()-2*matrix.std(), 
                            matrix.mean()+2*matrix.std() )
            elif args[1] is "auto3":
                #p1 = np.percentile(matrix, 10)  not in python 2.6.6?!
                #p2 = np.percentile(matrix, 90)
                p1 = sps.scoreatpercentile(np.hstack(matrix), 10)
                p2 = sps.scoreatpercentile(np.hstack(matrix), 90)
                imRange = p1-(p2-p1)/8, p2+(p2-p1)/8
            else:
                print "Error: range of %s is not recognized." % args[1]
                print "       please use a two element tuple or "
                print "       'auto', 'auto2' or 'auto3'"
                print "       enter 'showIm' for more info about options"
                return
        else:
            imRange = args[1][0], args[1][1]
    if len(args) > 2:   # zoom entered
        # no equivalent to matlab's pixelAxes in matplotlib. need dpi
        # might work with tkinter, but then have to change everything
        zoom = 1
    if len(args) > 3:   # label entered
        label = args[3]
    if len(args) > 4:   # colormap entered
        if args[4] is "auto":
            colormap = cm.Greys_r
        else:  # got a variable name
            colormap = args[4]
    if len(args) > 5 and args[5]:   # colorbar entered and set to true
        colorbar = args[5]
        
    #imgplot = plt.imshow(matrix, colormap, origin='lower').set_clim(imRange)
    imgplot = plt.imshow(matrix, colormap).set_clim(imRange)
    #plt.gca().invert_yaxis()  # default is inverted y from matlab
    if label != 0 and label != 1:
        plt.title(label)
    if colorbar:
        plt.colorbar(imgplot, cmap=cmap)
    #pylab.show()
    plt.show()
    
# Compute maximum pyramid height for given image and filter sizes.
# Specifically: the number of corrDn operations that can be sequentially
# performed when subsampling by a factor of 2.
def maxPyrHt(imsz, filtsz):
    if isinstance(imsz, int):
        imsz = (imsz, 1)
    if isinstance(filtsz, int):
        filtsz = (filtsz, 1)

    if len(imsz) == 1 and len(filtsz) == 1:
        imsz = (imsz[0], 1)
        filtsz = (filtsz[0], 1)
    elif len(imsz) == 1 and not any(f == 1 for f in filtsz):
            print "Error: cannot have a 1D 'image' and 2D filter"
            exit(1)
    elif len(imsz) == 1:
        imsz = (imsz[0], 1)
    elif len(filtsz) == 1:
        filtsz = (filtsz[0], 1)

    if imsz == 0:
        height = 0
    elif isinstance(imsz, tuple):
        if any( i < f for i,f in zip(imsz, filtsz) ):
            height = 0
        else:
            #if any( i == 1 for i in imsz):
            if imsz[0] == 1:
                imsz = (1, int(math.floor(imsz[1]/2) ) )
            elif imsz[1] == 1:
                imsz = (int( math.floor(imsz[0]/2) ), 1)
            else:
                imsz = ( int( math.floor(imsz[0]/2) ), 
                         int( math.floor(imsz[1]/2) ))
            height = 1 + maxPyrHt(imsz, filtsz)
    else:
        if any(imsz < f for f in filtsz):
            height = 0;
        else:
            imsz = ( int( math.floor(imsz/2) ), 1 )
            height = 1 + maxPyrHt(imsz, filtsz)
            
    return height

# returns a vector of binomial coefficients of order (size-1)
def binomialFilter(size):
    if size < 2:
        print "Error: size argument must be larger than 1"
        exit(1)
    
    kernel = np.array([[0.5], [0.5]])

    for i in range(0, size-2):
        kernel = spsig.convolve(np.array([[0.5], [0.5]]), kernel)

    return np.asarray(kernel)

# Some standard 1D filter kernels. These are scaled such that their L2-norm 
#   is 1.0
#
# binomN              - binomial coefficient filter of order N-1
# haar                - Harr wavelet
# qmf8, qmf12, qmf16  - Symmetric Quadrature Mirror Filters [Johnston80]
# daub2, daub3, daub4 - Daubechies wavelet [Daubechies88]
# qmf5, qmf9, qmf13   - Symmetric Quadrature Mirror Filters [Simoncelli88, 
#                                                            Simoncelli90]
# [Johnston80] - J D Johnston, "A filter family designed for use in quadrature 
#    mirror filter banks", Proc. ICASSP, pp 291-294, 1980.
#
# [Daubechies88] - I Daubechies, "Orthonormal bases of compactly supported wavelets",
#    Commun. Pure Appl. Math, vol. 42, pp 909-996, 1988.
#
# [Simoncelli88] - E P Simoncelli,  "Orthogonal sub-band image transforms",
#     PhD Thesis, MIT Dept. of Elec. Eng. and Comp. Sci. May 1988.
#     Also available as: MIT Media Laboratory Vision and Modeling Technical 
#     Report #100.
#
# [Simoncelli90] -  E P Simoncelli and E H Adelson, "Subband image coding",
#    Subband Transforms, chapter 4, ed. John W Woods, Kluwer Academic 
#    Publishers,  Norwell, MA, 1990, pp 143--192.
#
# Rob Young, 4/13
#
def namedFilter(name):
    if len(name) > 5 and name[:5] == "binom":
        kernel = math.sqrt(2) * binomialFilter(int(name[5:]))
    elif name is "qmf5":
        kernel = np.array([[-0.076103], [0.3535534], [0.8593118], [0.3535534], [-0.076103]])
    elif name is "qmf9":
        kernel = np.array([[0.02807382], [-0.060944743], [-0.073386624], [0.41472545], [0.7973934], [0.41472545], [-0.073386624], [-0.060944743], [0.02807382]])
    elif name is "qmf13":
        kernel = np.array([[-0.014556438], [0.021651438], [0.039045125], [-0.09800052], [-0.057827797], [0.42995453], [0.7737113], [0.42995453], [-0.057827797], [-0.09800052], [0.039045125], [0.021651438], [-0.014556438]])
    elif name is "qmf8":
        kernel = math.sqrt(2) * np.array([[0.00938715], [-0.07065183], [0.06942827], [0.4899808], [0.4899808], [0.06942827], [-0.07065183], [0.00938715]])
    elif name is "qmf12":
        kernel = math.sqrt(2) * np.array([[-0.003809699], [0.01885659], [-0.002710326], [-0.08469594], [0.08846992], [0.4843894], [0.4843894], [0.08846992], [-0.08469594], [-0.002710326], [0.01885659], [-0.003809699]])
    elif name is "qmf16":
        kernel = math.sqrt(2) * np.array([[0.001050167], [-0.005054526], [-0.002589756], [0.0276414], [-0.009666376], [-0.09039223], [0.09779817], [0.4810284], [0.4810284], [0.09779817], [-0.09039223], [-0.009666376], [0.0276414], [-0.002589756], [-0.005054526], [0.001050167]])
    elif name is "haar":
        kernel = np.array([[1], [1]]) / math.sqrt(2)
    elif name is "daub2":
        kernel = np.array([[0.482962913145], [0.836516303738], [0.224143868042], [-0.129409522551]]);
    elif name is "daub3":
        kernel = np.array([[0.332670552950], [0.806891509311], [0.459877502118], [-0.135011020010], [-0.085441273882], [0.035226291882]])
    elif name is "daub4":
        kernel = np.array([[0.230377813309], [0.714846570553], [0.630880767930], [-0.027983769417], [-0.187034811719], [0.030841381836], [0.032883011667], [-0.010597401785]])
    elif name is "gauss5":  # for backward-compatibility
        kernel = math.sqrt(2) * np.array([[0.0625], [0.25], [0.375], [0.25], [0.0625]])
    elif name is "gauss3":  # for backward-compatibility
        kernel = math.sqrt(2) * np.array([[0.25], [0.5], [0.25]])
    else:
        print "Error: Bad filter name: %s" % (name)
        exit(1)
    return np.array(kernel)

def strictly_decreasing(L):
    return all(x>y for x, y in zip(L, L[1:]))

def comparePyr(matPyr, pyPyr):
    # compare two pyramids - return 0 for !=, 1 for == 
    # correct number of elements?
    matSz = sum(matPyr.shape)
    pySz = 1
    for key in pyPyr.pyr.keys():
        if len(key) == 1:
            pySz += key[0]
        else:
            pySz += key[0] * key[1]

    if(matSz != pySz):
        print "size difference: returning 0"
        print matSz
        print pySz
        print pyPyr.pyr.keys()
        return 0

    # values are the same?
    matStart = 0
    sortedKeys = sorted(pyPyr.pyr.keys(), reverse=True, key=lambda element: 
                        (element[0], element[1]))
    for key in sortedKeys:
        bandSz = key
        matLen = bandSz[0] * bandSz[1]
        matTmp = matPyr[matStart:matStart + matLen]
        matTmp = np.reshape(matTmp, bandSz, order='F')
        matStart = matStart+matLen
        if (matTmp != pyPyr.pyr[key]).any():
            print "some pyramid elements not identical: checking..."
            for i in range(key[0]):
                for j in range(key[1]):
                    if matTmp[i,j] != pyPyr.pyr[key][i,j]:
                        if ( math.fabs(matTmp[i,j] - pyPyr.pyr[key][i,j]) > 
                             math.pow(10,-12) ):
                            #print "%.20f" % (math.fabs(matTmp[i,j] - 
                            #                           pyPyr.pyr[key][i,j]))
                            return 0
            print "same to 10^-12"
    return 1

def mkRamp(*args):
    # mkRamp(SIZE, DIRECTION, SLOPE, INTERCEPT, ORIGIN)
    # Compute a matrix of dimension SIZE (a [Y X] 2-vector, or a scalar)
    # containing samples of a ramp function, with given gradient DIRECTION
    # (radians, CW from X-axis, default = 0), SLOPE (per pixel, default = 
    # 1), and a value of INTERCEPT (default = 0) at the ORIGIN (default =
    # (size+1)/2, [1 1] = upper left). All but the first argument are
    # optional
    
    if len(args) == 0:
        print "mkRamp(SIZE, DIRECTION, SLOPE, INTERCEPT, ORIGIN)"
        print "first argument is required"
        exit(1)
    else:
        sz = args[0]
        if isinstance(sz, (int)):
            sz = (sz, sz)
        elif not isinstance(sz, (tuple)):
            print "first argument must be a two element tuple or an integer"
            exit(1)

    # OPTIONAL args:

    if len(args) > 1:
        direction = args[1]
    else:
        direction = 0

    if len(args) > 2:
        slope = args[2]
    else:
        slope = 1

    if len(args) > 3:
        intercept = args[3]
    else:
        intercept = 0

    if len(args) > 4:
        origin = args[4]
    else:
        origin = ( float(sz[0]-1)/2.0, float(sz[1]-1)/2.0 )

    #--------------------------

    xinc = slope * math.cos(direction)
    yinc = slope * math.sin(direction)

    [xramp, yramp] = np.meshgrid( xinc * (np.array(range(sz[1]))-origin[1]),
                                  yinc * (np.array(range(sz[0]))-origin[0]) )

    res = intercept + xramp + yramp

    return res.copy()
