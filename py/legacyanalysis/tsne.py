#
#  tsne.py
#
# Implementation of t-SNE in Python. The implementation was tested on Python 2.7.10, and it requires a working
# installation of NumPy. The implementation comes with an example on the MNIST dataset. In order to plot the
# results of this example, a working installation of matplotlib is required.
#
# The example can be run by executing: `ipython tsne.py`
#
#
#  Created by Laurens van der Maaten on 20-12-08.
#  Copyright (c) 2008 Tilburg University. All rights reserved.

# Note: on the download page, it says: 
#
# You are free to use, modify, or redistribute this software in any
# way you want, but only for non-commercial purposes. The use of the
# software is at your own risk; the authors are not responsible for
# any damage as a result from errors in the software.
#
# - https://lvdmaaten.github.io/tsne/ , 2017-04-28.
#
import numpy as Math
import pylab as Plot

def Hbeta(D = Math.array([]), beta = 1.0):
    """Compute the perplexity and the P-row for a specific value of the precision of a Gaussian distribution."""

    # Compute P-row and corresponding perplexity
    P = Math.exp(-D.copy() * beta);
    sumP = sum(P);
    H = Math.log(sumP) + beta * Math.sum(D * P) / sumP;
    P = P / sumP;
    return H, P;


def x2p(X = Math.array([]), tol = 1e-5, perplexity = 30.0):
    """Performs a binary search to get P-values in such a way that each conditional Gaussian has the same perplexity."""

    # Initialize some variables
    print "Computing pairwise distances..."
    (n, d) = X.shape;
    sum_X = Math.sum(Math.square(X), 1);
    D = Math.add(Math.add(-2 * Math.dot(X, X.T), sum_X).T, sum_X);
    P = Math.zeros((n, n));
    beta = Math.ones((n, 1));
    logU = Math.log(perplexity);

    # Loop over all datapoints
    for i in range(n):

        # Print progress
        if i % 500 == 0:
            print "Computing P-values for point ", i, " of ", n, "..."

        # Compute the Gaussian kernel and entropy for the current precision
        betamin = -Math.inf;
        betamax =  Math.inf;
        Di = D[i, Math.concatenate((Math.r_[0:i], Math.r_[i+1:n]))];
        (H, thisP) = Hbeta(Di, beta[i]);

        # Evaluate whether the perplexity is within tolerance
        Hdiff = H - logU;
        tries = 0;
        while Math.abs(Hdiff) > tol and tries < 50:

            # If not, increase or decrease precision
            if Hdiff > 0:
                betamin = beta[i].copy();
                if betamax == Math.inf or betamax == -Math.inf:
                    beta[i] = beta[i] * 2;
                else:
                    beta[i] = (beta[i] + betamax) / 2;
            else:
                betamax = beta[i].copy();
                if betamin == Math.inf or betamin == -Math.inf:
                    beta[i] = beta[i] / 2;
                else:
                    beta[i] = (beta[i] + betamin) / 2;

            # Recompute the values
            (H, thisP) = Hbeta(Di, beta[i]);
            Hdiff = H - logU;
            tries = tries + 1;

        # Set the final row of P
        P[i, Math.concatenate((Math.r_[0:i], Math.r_[i+1:n]))] = thisP;

    # Return final P-matrix
    print "Mean value of sigma: ", Math.mean(Math.sqrt(1 / beta));
    return P;


def pca(X = Math.array([]), no_dims = 50):
    """Runs PCA on the NxD array X in order to reduce its dimensionality to no_dims dimensions."""

    print "Preprocessing the data using PCA..."
    (n, d) = X.shape;
    X = X - Math.tile(Math.mean(X, 0), (n, 1));
    (l, M) = Math.linalg.eig(Math.dot(X.T, X));
    Y = Math.dot(X, M[:,0:no_dims]);
    return Y;


def tsne(X = Math.array([]), no_dims = 2, initial_dims = 50, perplexity = 30.0):
    """Runs t-SNE on the dataset in the NxD array X to reduce its dimensionality to no_dims dimensions.
    The syntaxis of the function is Y = tsne.tsne(X, no_dims, perplexity), where X is an NxD NumPy array."""

    # Check inputs
    if isinstance(no_dims, float):
        print "Error: array X should have type float.";
        return -1;
    if round(no_dims) != no_dims:
        print "Error: number of dimensions should be an integer.";
        return -1;

    # Initialize variables
    X = pca(X, initial_dims).real;
    (n, d) = X.shape;
    max_iter = 1000;
    initial_momentum = 0.5;
    final_momentum = 0.8;
    eta = 500;
    min_gain = 0.01;
    Y = Math.random.randn(n, no_dims);
    dY = Math.zeros((n, no_dims));
    iY = Math.zeros((n, no_dims));
    gains = Math.ones((n, no_dims));

    # Compute P-values
    P = x2p(X, 1e-5, perplexity);
    P = P + Math.transpose(P);
    P = P / Math.sum(P);
    P = P * 4;                                  # early exaggeration
    P = Math.maximum(P, 1e-12);

    # Run iterations
    for iter in range(max_iter):

        # Compute pairwise affinities
        sum_Y = Math.sum(Math.square(Y), 1);
        num = 1 / (1 + Math.add(Math.add(-2 * Math.dot(Y, Y.T), sum_Y).T, sum_Y));
        num[range(n), range(n)] = 0;
        Q = num / Math.sum(num);
        Q = Math.maximum(Q, 1e-12);

        # Compute gradient
        PQ = P - Q;
        for i in range(n):
            dY[i,:] = Math.sum(Math.tile(PQ[:,i] * num[:,i], (no_dims, 1)).T * (Y[i,:] - Y), 0);

        # Perform the update
        if iter < 20:
            momentum = initial_momentum
        else:
            momentum = final_momentum
        gains = (gains + 0.2) * ((dY > 0) != (iY > 0)) + (gains * 0.8) * ((dY > 0) == (iY > 0));
        gains[gains < min_gain] = min_gain;
        iY = momentum * iY - eta * (gains * dY);
        Y = Y + iY;
        Y = Y - Math.tile(Math.mean(Y, 0), (n, 1));

        # Compute current value of cost function
        if iter < 200 or (iter + 1) % 10 == 0:
            C = Math.sum(P * Math.log(P / Q));
            print "Iteration ", (iter + 1), ": error is ", C

            # Plot.clf()
            # Plot.scatter(Y[:,0], Y[:,1], s=20, c=labels,
            #              vmin=labels.min(), vmax=labels.max());
            # Plot.savefig('step-%04i.png' % iter)
            # ax = plt.axis()
            #mx = np.max(np.abs(ax))
            #xlo,xhi, ylo,yhi = ax

            #xlo,xhi = Y[:,0].min(), Y[:,0].max()
            #ylo,yhi = Y[:,1].min(), Y[:,1].max()
            mx = Math.abs(Y).max()
            xlo,xhi = -mx,mx
            #mx = Math.abs(Y[:,1]).max()
            ylo,yhi = -mx,mx
            Plot.clf()
            #S = mx * 0.05
            #Plot.clf()
            ih,iw = 400,400
            imgmap = np.zeros((ih,iw,3), np.uint8)
            for i in range(n):
                x = Y[i,0]
                y = Y[i,1]
                #Plot.imshow(stamps[i], extent=[x-S,x+S, y-S,y+S],
                #            interpolation='nearest', origin='lower')
                ix = int((x - xlo) / (xhi - xlo) * iw)
                iy = int((y - ylo) / (yhi - ylo) * ih)
                sh,sw,d = stamps[i].shape
                ix = int(np.clip(ix-sw/2, 0, iw-sw))
                iy = int(np.clip(iy-sh/2, 0, ih-sh))
                imgmap[iy : iy+sh, ix : ix+sw, :] = np.maximum(
                    imgmap[iy : iy+sh, ix : ix+sw, :], stamps[i])
            # Plot.axis([-(mx+S), mx+S, -(mx+S), mx+S])
            Plot.imshow(imgmap, interpolation='nearest', origin='lower')
            Plot.xticks([]); Plot.yticks([])
            Plot.title('t-SNE on DECaLS catalogs: %s' % samplename)
            Plot.savefig('stamp-%04i.png' % iter)

            
        # Stop lying about P-values
        if iter == 100:
            P = P / 4;

    # Return solution
    return Y;


if __name__ == "__main__":
    #X = Math.loadtxt("mnist2500_X.txt");
    #labels = Math.loadtxt("mnist2500_labels.txt");
    #X = X[:500,:]
    #labels = labels[:500]

    from astrometry.util.fits import *
    import pylab as plt
    from collections import Counter
    

    #T = fits_table('~/legacypipe/py/cosmos-52-rex2/tractor/150/tractor-1501p025.fits')
    TT = []
    for brick in ['1498p017', '1498p020', '1498p022', '1498p025', '1501p017', '1501p020', '1501p022', '1501p025', '1503p017', '1503p020', '1503p022', '1503p025', '1506p017', '1506p020', '1506p022', '1506p025']:
        B = brick[:3]
        T = fits_table('~/legacypipe/py/cosmos-50-rex2/metrics/%s/all-models-%s.fits' % (B,brick))
        T2 = fits_table('~/legacypipe/py/cosmos-50-rex2/tractor/%s/tractor-%s.fits' % (B,brick))
        jpg = plt.imread('/Users/dstn/legacypipe/py/cosmos-50-rex2/coadd/%s/%s/legacysurvey-%s-image.jpg' % (B,brick,brick))

        T.decam_flux = T2.decam_flux
        T.decam_flux_ivar = T2.decam_flux_ivar
        T.bx = T2.bx
        T.by = T2.by

        T.ix = np.round(T.bx).astype(int)
        T.iy = np.round(T.by).astype(int)
        jpg = np.flipud(jpg)
        H,W,d = jpg.shape
        S = 15
        #print(jpg.shape, jpg.dtype)
        T.cut((T.ix >= S) * (T.iy >= S) * (T.ix < (W-S)) * (T.iy < (H-S)))
        stamps = []
        for i in range(len(T)):
            stamps.append((jpg[T.iy[i] - S : T.iy[i] + S + 1,
                               T.ix[i] - S : T.ix[i] + S + 1, :]))
        T.stamps = stamps
        TT.append(T)
    T = merge_tables(TT)

    print(len(T))
    T.labels = np.zeros(len(T), int)
    T.labels[T.type == 'REX '] = 1
    T.labels[T.type == 'EXP '] = 2
    T.labels[T.type == 'DEV '] = 3
    T.labels[T.type == 'COMP'] = 4
    T.g = -2.5 * (np.log10(T.decam_flux[:,1]) - 9)
    T.r = -2.5 * (np.log10(T.decam_flux[:,2]) - 9)
    T.z = -2.5 * (np.log10(T.decam_flux[:,4]) - 9)
    print(Counter(T.type))
    T.cut(np.isfinite(T.g) * np.isfinite(T.r) * np.isfinite(T.z))
    print('Finite mags:', Counter(T.type))
    T.cut((T.g > 15) * (T.g < 25) *
          (T.r > 15) * (T.r < 25) *
          (T.z > 15) * (T.z < 25))
    print('Mags 15 to 25:', Counter(T.type))
    # T.cut((T.g > 15) * (T.g < 23) *
    #       (T.r > 15) * (T.r < 23) *
    #       (T.z > 15) * (T.z < 23))
    print(len(T))

    mg = np.median(T.decam_flux_ivar[:,1])
    mr = np.median(T.decam_flux_ivar[:,2])
    mz = np.median(T.decam_flux_ivar[:,4])
    T.cut((T.decam_flux_ivar[:,1] > mg/4.) *
          (T.decam_flux_ivar[:,2] > mr/4.) *
          (T.decam_flux_ivar[:,4] > mz/4.))
    print(len(T))
    print('Invvars:', Counter(T.type))
    
    #T.cut(np.logical_or(T.type == 'EXP ', T.type == 'DEV '))
    #T.cut(T.type == 'EXP ')
    #samplename = 'EXP galaxies'
    # T.cut(T.type == 'DEV ')
    # samplename = 'DEV galaxies'
    #T = T[np.argsort(T.r)[:500]]

    #T.cut(T.type == 'REX ')
    #T.cut(T.r < 21)
    #samplename = 'REX sources'
    
    #T.cut(np.logical_or(np.logical_or(T.type == 'EXP ', T.type == 'DEV '), T.type == 'REX '))

    T.cut(T.r < 21)
    samplename = 'r < 21'
    
    #T = T[:500]
    T = T[:1000]

    print('Sample:', Counter(T.type))

    print(Counter(T.type))
    labels = T.labels
    stamps = T.stamps
    
    X = np.vstack((T.r, T.g - T.r, T.r - T.z,
                   T.rex_shapeexp_r)).T

    assert(np.all(np.isfinite(X)))
    print(X.shape)

    D = X.shape[1]
    for i in range(D):
        for j in range(i):
            plt.clf()
            plt.plot(X[i,:], X[j,:], 'b.')
            plt.savefig('x-%i-%i.png' % (i,j))
    
    Y = tsne(X, 2, 50, 20.0);
    # Plot.scatter(Y[:,0], Y[:,1], s=20, c=labels,
    #                      vmin=labels.min(), vmax=labels.max());
    # Plot.show();
    # Plot.savefig('1.png')
