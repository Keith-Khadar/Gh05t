# Signal Pre-processing

While using raw signals in training is possible, it is often more advisable to use important signal features. The study of important signal features is called Component Analysis, and in the context of these signals, we care about **Independent Component Analysis**.

## Inexpensive vs. Expensive

### Inexpensive

Normalized Least Mean Squares Algorithm. By gathering the error of a reference error signal and the input signal that likely contains relevant information, it is possible to reduce the noise and amplify the true signal.

### Expensive

Variable Step Size Affine Projection Algorithm. Like Normalized Least Mean Squares Algorithm, this algorithm gathers the signal's previous data windows to enhance the prediction ability, however this increases the compute necessary as well.

Information Theoretic Stochastic Deconvolution. This uses the principle of maximizing output entropy to maximize the output's information content w.r.t. the observed signal. This can also operate online but requires an appropriate desired signal (this can be through empirical observation or approximation). 

## Usage

For NLMS and VSSAPA, there are the apply_x() functions, which apply 1 iteration of the machine learning algorithm. The infomax deconvolution has the info_max_deconvolution_parzen_window_sampler() which will be renamed soon to reflect the other algorithm names - again this applies 1 iteration of the machine learning algorithm.


