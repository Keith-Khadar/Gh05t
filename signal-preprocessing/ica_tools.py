import numpy as np
import cupy as cp
from scipy.linalg import sqrtm  # Use scipy's sqrtm for robustness

def fast_ica(X: np.ndarray, out_channels: int, preprocess: str = "whiten", Cost: str = "Kurtosis", iterations: int = 256, threshold: float = 1e-6, PU: str = "CPU"):
    """
    FastICA algorithm for independent component analysis.
    :param X: Input data matrix of shape (samples, in_channels)
    :param out_channels: Number of independent components to extract
    :param preprocess: Preprocessing method ("whiten" or None)
    :param Cost: Nonlinearity to use ("Kurtosis" or "Negentropy")
    :param iterations: Maximum number of iterations
    :param threshold: Convergence threshold
    :param PU: Processing unit ("CPU" or "GPU")
    :return: Unmixing matrix W, independent components S
    """
    # Ensure X is of shape (samples, in_channels)
    samples, in_channels = X.shape
    print("Input Shape: ", X.shape)

    if PU == "CPU":
        # Centering
        X -= np.mean(X, axis=0, keepdims=True)
        # Normalize
        norms = np.linalg.norm(X, axis=0, keepdims=True)
        X /= np.where(norms == 0, 1, norms)

        # Whitening
        if preprocess == 'whiten':
            cov_X = np.cov(X, rowvar=False)
            eigvals, eigvecs = np.linalg.eigh(cov_X)
            D_inv_sqrt = np.diag(1.0 / np.sqrt(eigvals))
            whitening_matrix = eigvecs @ D_inv_sqrt @ eigvecs.T
            X = X @ whitening_matrix

        print("Whitened Shape: ", X.shape)
        print("Has NaN or Inf: ", np.isnan(X).any() or np.isinf(X).any())

        # Initialize W
        W = np.random.rand(out_channels, in_channels)
        W /= np.linalg.norm(W, axis=1, keepdims=True)

        # Select nonlinearity
        if Cost == "Kurtosis":
            g = lambda u: u ** 3
            g_prime = lambda u: 3 * u ** 2
        elif Cost == "Negentropy":
            g = lambda u: np.tanh(u)
            g_prime = lambda u: 1 - np.tanh(u) ** 2
        else:
            raise ValueError("Invalid cost function")

        for iter_num in range(iterations):
            print("Iteration: ", iter_num)
            S = X @ W.T  # Shape: (samples, out_channels)
            Y = g(S)
            Y_prime = g_prime(S)

            # Update rule
            W_new = (Y.T @ X) / samples - np.diag(Y_prime.mean(axis=0)) @ W

            # Symmetric orthogonalization using SVD
            U, _, Vt = np.linalg.svd(W_new, full_matrices=False)
            W_new = U @ Vt

            # Convergence check
            delta = np.max(np.abs(np.abs(np.diag(W_new @ W.T)) - 1))
            if delta < threshold:
                print("Converged at iteration:", iter_num)
                break

            W = W_new

        S = X @ W.T

    elif PU == "GPU":
        # Similar adjustments for GPU using CuPy
        pass
    else:
        raise ValueError("Invalid Processing Unit")

    return W, S


def infomax_ica(X: np.ndarray, out_channels: int, preprocess: str = "whiten", learning_rate: float = 0.01, iterations: int = 1000, threshold: float = 1e-6):
    """
    Infomax ICA algorithm for independent component analysis.
    :param X: Input data matrix of shape (channels, samples)
    :param out_channels: Number of independent components to extract
    :param preprocess: Preprocessing method ("whiten" or None)
    :param learning_rate: Learning rate for gradient ascent
    :param iterations: Maximum number of iterations
    :param threshold: Convergence threshold
    :return: Unmixing matrix W
    """
    # Get dimensions
    in_channels, samples = X.shape

    # Centering
    X = X - np.mean(X, axis=1, keepdims=True)

    # Whitening
    if preprocess == 'whiten':
        cov_X = np.cov(X)
        eigvals, eigvecs = np.linalg.eigh(cov_X)
        D_inv_sqrt = np.diag(1.0 / np.sqrt(eigvals))
        whitening_matrix = D_inv_sqrt @ eigvecs.T
        X = whitening_matrix @ X

    # Initialize W
    W = np.random.rand(out_channels, in_channels)
    W = W / np.linalg.norm(W, axis=1, keepdims=True)

    for _ in range(iterations):
        WX = W @ X  # Shape: (out_channels, samples)
        Y = 1 / (1 + np.exp(-WX))  # Sigmoid activation function

        # Natural gradient update
        delta_W = learning_rate * ((samples * np.eye(out_channels) + (1 - 2 * Y) @ WX.T) @ W)

        W_new = W + delta_W

        # Normalize rows of W
        W_new = W_new / np.linalg.norm(W_new, axis=1, keepdims=True)

        # Convergence check
        delta = np.max(np.abs(np.abs(np.diag(W_new @ W.T)) - 1))
        if delta < threshold:
            break

        W = W_new

    return W

def jade_ica(X: np.ndarray, out_channels: int, preprocess: str = "whiten"):
    """
    JADE algorithm for independent component analysis.
    :param X: Input data matrix of shape (channels, samples)
    :param out_channels: Number of independent components to extract
    :param preprocess: Preprocessing method ("whiten" or None)
    :return: Unmixing matrix W
    """
    # Get dimensions
    in_channels, samples = X.shape

    # Centering
    X = X - np.mean(X, axis=1, keepdims=True)

    # Whitening
    if preprocess == 'whiten':
        cov_X = np.cov(X)
        eigvals, eigvecs = np.linalg.eigh(cov_X)
        D_inv_sqrt = np.diag(1.0 / np.sqrt(eigvals))
        whitening_matrix = D_inv_sqrt @ eigvecs.T
        X_white = whitening_matrix @ X
    else:
        X_white = X

    # Estimate the cumulant matrices
    def compute_cumulant_matrices(X):
        n, T = X.shape
        cumulant_matrices = np.zeros((n, n, n, n))
        for t in range(T):
            x = X[:, t]
            cumulant_matrices += np.outer(np.outer(x, x), np.outer(x, x)).reshape(n, n, n, n)
        cumulant_matrices = cumulant_matrices / T

        # Subtract the Gaussian part
        for i in range(n):
            cumulant_matrices[i, i, :, :] -= np.eye(n)
            cumulant_matrices[:, :, i, i] -= np.eye(n)
        return cumulant_matrices

    cumulant_matrices = compute_cumulant_matrices(X_white)

    # Reshape the cumulant tensors into matrices
    n = in_channels
    m = n * (n + 1) // 2
    cumulant_vectors = np.zeros((m, n * n))
    idx = 0
    for i in range(n):
        for j in range(i, n):
            Qij = cumulant_matrices[i, j, :, :] + cumulant_matrices[j, i, :, :]
            if i != j:
                Qij = Qij + cumulant_matrices[i, j, :, :].T + cumulant_matrices[j, i, :, :].T
            Qij = Qij / 2.0
            cumulant_vectors[idx, :] = Qij.reshape(-1)
            idx += 1

    # Joint diagonalization
    U, _, _ = np.linalg.svd(cumulant_vectors)
    W = U[:, :out_channels].T

    # Compute the unmixing matrix
    W = W @ whitening_matrix

    return W

def extended_infomax_ica(X: np.ndarray, out_channels: int, preprocess: str = "whiten", learning_rate: float = 0.01, iterations: int = 1000, threshold: float = 1e-6):
    """
    Extended Infomax ICA algorithm for independent component analysis.
    :param X: Input data matrix of shape (channels, samples)
    :param out_channels: Number of independent components to extract
    :param preprocess: Preprocessing method ("whiten" or None)
    :param learning_rate: Learning rate for gradient ascent
    :param iterations: Maximum number of iterations
    :param threshold: Convergence threshold
    :return: Unmixing matrix W
    """
    # Get dimensions
    in_channels, samples = X.shape

    # Centering
    X = X - np.mean(X, axis=1, keepdims=True)

    # Whitening
    if preprocess == 'whiten':
        cov_X = np.cov(X)
        eigvals, eigvecs = np.linalg.eigh(cov_X)
        D_inv_sqrt = np.diag(1.0 / np.sqrt(eigvals))
        whitening_matrix = D_inv_sqrt @ eigvecs.T
        X = whitening_matrix @ X

    # Initialize W
    W = np.random.rand(out_channels, in_channels)
    W = W / np.linalg.norm(W, axis=1, keepdims=True)

    # Initialize beta parameters
    beta = np.ones((out_channels, 1))

    for _ in range(iterations):
        WX = W @ X  # Shape: (out_channels, samples)
        Y = np.tanh(beta * WX)  # Nonlinear function
        Y_prime = beta * (1 - np.tanh(beta * WX) ** 2)  # Derivative

        # Update beta adaptively based on kurtosis
        kurtosis = np.mean(WX ** 4, axis=1) - 3
        beta = np.sign(kurtosis).reshape(-1, 1)

        # Natural gradient update
        delta_W = learning_rate * ((samples * np.eye(out_channels) + Y @ WX.T) @ W)

        W_new = W + delta_W

        # Normalize rows of W
        W_new = W_new / np.linalg.norm(W_new, axis=1, keepdims=True)

        # Convergence check
        delta = np.max(np.abs(np.abs(np.diag(W_new @ W.T)) - 1))
        if delta < threshold:
            break

        W = W_new

    return W