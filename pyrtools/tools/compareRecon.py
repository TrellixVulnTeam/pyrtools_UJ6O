import numpy
import math

def compareRecon(recon1, recon2, rtol=1e-5, atol=1e-8):
    ''' compare two arrays and return 1 is they are the same within specified
        precision and 0 if not.
        function was made to accompany unit test code '''

    # NOTE builtin numpy:
    # np.allclose(recon1, recon2, rtol=1e-05, atol=1e-08, equal_nan=False)
    # BUT won't print where and what the first error is

    if recon1.shape != recon2.shape:
        print('shape is different!')
        print(recon1.shape)
        print(recon2.shape)
        return 0

    for i in range(recon1.shape[0]):
        for j in range(recon2.shape[1]):
            if numpy.absolute(recon1[i,j].real - recon2[i,j].real) > math.pow(10,-11):
                print("real: i=%d j=%d %.15f %.15f diff=%.15f" % (i, j, recon1[i,j].real, recon2[i,j].real, numpy.absolute(recon1[i,j].real-recon2[i,j].real)))
                return 0
            ## FIX: need a better way to test
            # if we have many significant digits to the left of decimal we
            #   need to be less stringent about digits to the right.
            # The code below works, but there must be a better way.
            if isinstance(recon1, complex):
                if int(math.log(numpy.abs(recon1[i,j].imag), 10)) > 1:
                    prec = prec + int(math.log(numpy.abs(recon1[i,j].imag), 10))
                    if prec > 0:
                        prec = -1
                print(prec)
                if numpy.absolute(recon1[i,j].imag - recon2[i,j].imag) > math.pow(10, prec):
                    print("imag: i=%d j=%d %.15f %.15f diff=%.15f" % (i, j, recon1[i,j].imag, recon2[i,j].imag, numpy.absolute(recon1[i,j].imag-recon2[i,j].imag)))
                    return 0

    return 1
