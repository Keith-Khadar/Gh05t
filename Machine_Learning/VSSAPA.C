#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

// ------------------------------
// Data Structures and CSV Loading Functions
// ------------------------------

typedef struct {
    double *time;
    double *voltage;
    int n;
} Data;

// Count the number of data lines (excluding header) in the CSV file.
int count_lines(const char *filename) {
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        printf("Error opening file %s\n", filename);
        return 0;
    }
    char line[1024];
    int count = 0;
    // Skip header line.
    if (fgets(line, sizeof(line), fp) == NULL) {
        fclose(fp);
        return 0;
    }
    while (fgets(line, sizeof(line), fp)) {
        count++;
    }
    fclose(fp);
    return count;
}

// Load a CSV file and extract the "Time" and "Channel1" columns.
// Assumes a header line and that each line has three comma‐separated values.
Data* load_csv(const char *filename) {
    int n = count_lines(filename);
    if (n <= 0) {
        return NULL;
    }
    Data *data = (Data*) malloc(sizeof(Data));
    data->n = n;
    data->time = (double*) malloc(n * sizeof(double));
    data->voltage = (double*) malloc(n * sizeof(double));
    
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        printf("Error opening file %s\n", filename);
        free(data->time);
        free(data->voltage);
        free(data);
        return NULL;
    }
    
    char line[1024];
    // Read header line.
    if (fgets(line, sizeof(line), fp) == NULL) {
        fclose(fp);
        free(data->time);
        free(data->voltage);
        free(data);
        return NULL;
    }
    
    int index = 0;
    while (fgets(line, sizeof(line), fp)) {
        double t, ch1, ch2;
        // Expecting each line to have three comma-separated numbers.
        if (sscanf(line, "%lf,%lf,%lf", &t, &ch1, &ch2) == 3) {
            data->time[index] = t;
            data->voltage[index] = ch1;
            index++;
        }
    }
    fclose(fp);
    return data;
}

// ------------------------------
// Matrix Inversion Helper (for small matrices)
// ------------------------------

/*
  Inverts an n×n matrix A (stored in row-major order).
  The inverse is stored in A_inv.
  Returns 1 on success, 0 if the matrix is singular.
*/
int invert_matrix(const double *A, double *A_inv, int n) {
    int i, j, k;
    // Create an augmented matrix (n x 2n)
    double *aug = (double *) malloc(n * 2 * n * sizeof(double));
    if (!aug) return 0;
    // Build [A | I]
    for (i = 0; i < n; i++) {
        for (j = 0; j < n; j++) {
            aug[i * 2 * n + j] = A[i * n + j];
        }
        for (j = 0; j < n; j++) {
            aug[i * 2 * n + (n + j)] = (i == j) ? 1.0 : 0.0;
        }
    }
    // Gauss-Jordan elimination
    for (i = 0; i < n; i++) {
        double pivot = aug[i * 2 * n + i];
        if (fabs(pivot) < 1e-12) {
            free(aug);
            return 0; // Singular matrix
        }
        // Scale row i so that pivot becomes 1
        for (j = 0; j < 2 * n; j++) {
            aug[i * 2 * n + j] /= pivot;
        }
        // Eliminate pivot from other rows
        for (k = 0; k < n; k++) {
            if (k == i) continue;
            double factor = aug[k * 2 * n + i];
            for (j = 0; j < 2 * n; j++) {
                aug[k * 2 * n + j] -= factor * aug[i * 2 * n + j];
            }
        }
    }
    // Extract inverse matrix from augmented matrix
    for (i = 0; i < n; i++) {
        for (j = 0; j < n; j++) {
            A_inv[i * n + j] = aug[i * 2 * n + (n + j)];
        }
    }
    free(aug);
    return 1;
}

// ------------------------------
// VSS-APA Filter Functions
// ------------------------------

/*
  Applies one iteration of the VSS-APA filter.
  
  Parameters:
    X: pointer to an M×P input matrix (stored in row-major order),
       where element (i, p) is at X[i*P + p].
    d_vec: desired output vector of length P (future samples).
    w: current filter weight vector of length M.
    mu: current step size.
    delta: regularization parameter.
    M: filter order.
    P: projection order.
    
  Outputs:
    w_new: updated filter weights (length M).
    y_vec: output vector (length P) computed as X^T * w.
    e_vec: error vector (length P), where e = d_vec - y_vec.
*/
void apply_vss_apa_filter(const double *X, const double *d_vec, const double *w,
                            double mu, double delta, int M, int P,
                            double *w_new, double *y_vec, double *e_vec) {
    int i, p;
    // Compute y_vec = X^T * w (length P)
    for (p = 0; p < P; p++) {
        y_vec[p] = 0.0;
        for (i = 0; i < M; i++) {
            y_vec[p] += X[i * P + p] * w[i];
        }
    }
    // Compute error vector: e_vec = d_vec - y_vec
    for (p = 0; p < P; p++) {
        e_vec[p] = d_vec[p] - y_vec[p];
    }
    
    // Compute matrix A = X^T * X + delta * I (size P×P)
    double *A = (double *) malloc(P * P * sizeof(double));
    for (p = 0; p < P; p++) {
        for (int q = 0; q < P; q++) {
            double sum = 0.0;
            for (i = 0; i < M; i++) {
                sum += X[i * P + p] * X[i * P + q];
            }
            if (p == q) {
                A[p * P + q] = sum + delta;
            } else {
                A[p * P + q] = sum;
            }
        }
    }
    
    // Invert matrix A (result stored in A_inv)
    double *A_inv = (double *) malloc(P * P * sizeof(double));
    if (!invert_matrix(A, A_inv, P)) {
        printf("Matrix inversion failed (singular matrix).\n");
        free(A);
        free(A_inv);
        return;
    }
    
    // Compute temp = A_inv * e_vec (length P)
    double *temp = (double *) malloc(P * sizeof(double));
    for (p = 0; p < P; p++) {
        temp[p] = 0.0;
        for (int q = 0; q < P; q++) {
            temp[p] += A_inv[p * P + q] * e_vec[q];
        }
    }
    
    // Compute update vector u = X * temp (length M)
    double *u = (double *) malloc(M * sizeof(double));
    for (i = 0; i < M; i++) {
        u[i] = 0.0;
        for (p = 0; p < P; p++) {
            u[i] += X[i * P + p] * temp[p];
        }
    }
    
    // Update filter weights: w_new = w + mu * u
    for (i = 0; i < M; i++) {
        w_new[i] = w[i] + mu * u[i];
    }
    
    free(A);
    free(A_inv);
    free(temp);
    free(u);
}

/*
  Applies the VSS-APA filter (with variable step size) over the entire input sequence
  for future sample prediction.
  
  Parameters:
    x: input signal array (length N).
    d: desired signal array (length N).
    N: number of samples.
    M: filter order.
    P: projection order.
    mu0: initial step size.
    delta: regularization parameter.
    mu_min: minimum allowed step size.
    mu_max: maximum allowed step size.
    rho: adaptation rate for the step size.
    eta: target error energy threshold.
    alpha: exponential smoothing factor for error energy.
    beta: momentum factor for step-size adaptation.
    prediction_horizon: how many steps ahead to predict (e.g., 1 for one-step ahead).
    
  Outputs (pre-allocated by the caller):
    predictions: array of future predictions (length num_iterations).
    w_hist: 2D array (num_iterations x M) storing the weight vector at each iteration.
    mu_history: array (length num_iterations) of step sizes.
    error_hist: 2D array (num_iterations x P) of error vectors.
    
  The number of iterations is:
      num_iterations = N - (M + P - 1 + prediction_horizon)
  It is the number of blocks that can be formed.
*/
void vss_apa_filter_full(const double *x, const double *d, int N, int M, int P,
                           double mu0, double delta, double mu_min, double mu_max,
                           double rho, double eta, double alpha, double beta,
                           int prediction_horizon,
                           double *predictions, double **w_hist, double *mu_history, double **error_hist) {
    int start_index = M + P - 1;
    int num_iterations = N - (start_index + prediction_horizon);
    int k, p, i;
    
    // Initialize filter weights to zero.
    double *w = (double *) calloc(M, sizeof(double));
    // Temporary array to hold updated weights.
    double *w_new = (double *) malloc(M * sizeof(double));
    
    double mu = mu0;
    double error_energy_prev = eta; // initialize with target error energy
    
    // Loop over each block.
    for (k = start_index; k < start_index + num_iterations; k++) {
        // Allocate and build the input matrix X (dimensions M x P)
        double *X = (double *) malloc(M * P * sizeof(double));
        // For each projection index p: 
        //   idx_end = k - p, idx_start = idx_end - M + 1, then fill column p.
        for (p = 0; p < P; p++) {
            int idx_end = k - p;
            int idx_start = idx_end - M + 1;
            for (i = 0; i < M; i++) {
                X[i * P + p] = x[idx_start + i];
            }
        }
        
        // Build the desired output vector d_vec (length P) using future samples.
        // For each p, d_vec[p] = d[k + prediction_horizon - p]
        double *d_vec = (double *) malloc(P * sizeof(double));
        for (p = 0; p < P; p++) {
            d_vec[p] = d[k + prediction_horizon - p];
        }
        
        // Allocate arrays to hold the filter output and error for this block.
        double *y_vec = (double *) malloc(P * sizeof(double));
        double *e_vec = (double *) malloc(P * sizeof(double));
        
        // Apply one iteration of the VSS-APA filter.
        apply_vss_apa_filter(X, d_vec, w, mu, delta, M, P, w_new, y_vec, e_vec);
        
        // Save the prediction (corresponding to the first element of y_vec).
        predictions[k - start_index] = y_vec[0];
        // Save current filter weights.
        for (i = 0; i < M; i++) {
            w_hist[k - start_index][i] = w_new[i];
        }
        // Save the error vector.
        for (p = 0; p < P; p++) {
            error_hist[k - start_index][p] = e_vec[p];
        }
        
        // Compute error energy.
        double error_energy = 0.0;
        for (p = 0; p < P; p++) {
            error_energy += e_vec[p] * e_vec[p];
        }
        // Exponential smoothing of error energy.
        double error_energy_smoothed = alpha * error_energy_prev + (1 - alpha) * error_energy;
        // Compute RMS error (using mean squared error).
        double rms_error = sqrt(error_energy / P + 1e-6);
        double mu_update = rho * (error_energy_smoothed - eta) / (rms_error + 1e-6);
        
        // Update mu with momentum.
        mu = beta * mu + (1 - beta) * mu_update;
        if (mu < mu_min) mu = mu_min;
        if (mu > mu_max) mu = mu_max;
        mu_history[k - start_index] = mu;
        
        error_energy_prev = error_energy_smoothed;
        
        // Copy the updated weights for the next iteration.
        for (i = 0; i < M; i++) {
            w[i] = w_new[i];
        }
        
        free(X);
        free(d_vec);
        free(y_vec);
        free(e_vec);
    }
    
    free(w);
    free(w_new);
}

// ------------------------------
// Main Program
// ------------------------------
int main() {
    // Filter/adaptation parameters.
    int M = 4;               // Filter order
    int P = 1;               // Projection order (e.g., 1 for one-step prediction with one input vector)
    double mu0 = 0.1;        // Initial step size
    double delta = 0.001;    // Regularization parameter
    double mu_min = 0.01;    // Minimum step size
    double mu_max = 1.0;     // Maximum step size
    double rho = 0.05;       // Step-size adaptation rate
    double eta = 0.001;      // Target error energy threshold
    double alpha = 0.9;      // Exponential smoothing factor
    double beta = 0.8;       // Momentum factor for step-size adaptation
    int prediction_horizon = 1; // One-step ahead prediction

    // Process 10 files: eye_blinking0.csv to eye_blinking9.csv.
    for (int i = 0; i < 10; i++) {
        char filename[256];
        sprintf(filename, "eye_blinking%d.csv", i);
        
        // Load the data.
        Data *data = load_csv(filename);
        if (data == NULL) {
            printf("Failed to load %s\n", filename);
            continue;
        }
        int N = data->n;
        if (N < 1) {
            printf("Not enough data in %s\n", filename);
            free(data->time);
            free(data->voltage);
            free(data);
            continue;
        }
        
        // Determine number of iterations.
        int start_index = M + P - 1;
        int num_iterations = N - (start_index + prediction_horizon);
        if (num_iterations <= 0) {
            printf("Not enough samples for filtering in %s\n", filename);
            free(data->time);
            free(data->voltage);
            free(data);
            continue;
        }
        
        // Allocate memory for outputs.
        double *predictions = (double *) malloc(num_iterations * sizeof(double));
        double *mu_history = (double *) malloc(num_iterations * sizeof(double));
        
        // Allocate weight history (num_iterations x M) and error history (num_iterations x P).
        double **w_hist = (double **) malloc(num_iterations * sizeof(double *));
        double **error_hist = (double **) malloc(num_iterations * sizeof(double *));
        for (int n = 0; n < num_iterations; n++) {
            w_hist[n] = (double *) malloc(M * sizeof(double));
            error_hist[n] = (double *) malloc(P * sizeof(double));
        }
        
        // Apply the VSS-APA filter.
        vss_apa_filter_full(data->voltage, data->voltage, N, M, P, mu0, delta,
                            mu_min, mu_max, rho, eta, alpha, beta, prediction_horizon,
                            predictions, w_hist, mu_history, error_hist);
        
        // Compute NMSE: norm(e_hist) / norm(voltage segment)
        double norm_e = 0.0, norm_volt = 0.0;
        // Sum errors over all iterations and across the P-length error vector.
        for (int n = 0; n < num_iterations; n++) {
            for (int p = 0; p < P; p++) {
                norm_e += error_hist[n][p] * error_hist[n][p];
            }
        }
        // Use the corresponding segment of the true signal.
        for (int n = start_index + prediction_horizon; n < start_index + prediction_horizon + num_iterations; n++) {
            norm_volt += data->voltage[n] * data->voltage[n];
        }
        norm_e = sqrt(norm_e);
        norm_volt = sqrt(norm_volt);
        double nmse = norm_e / norm_volt;
        printf("File %s, NMSE: %lf\n", filename, nmse);
        
        // Write predictions to a CSV file (e.g., output0.csv).
        char out_filename[256];
        sprintf(out_filename, "output%d.csv", i);
        FILE *out_fp = fopen(out_filename, "w");
        if (out_fp) {
            fprintf(out_fp, "Time,TrueVoltage,Prediction\n");
            // The predictions correspond to indices starting at (start_index+prediction_horizon)
            for (int n = 0; n < num_iterations; n++) {
                int idx = start_index + prediction_horizon + n;
                fprintf(out_fp, "%lf,%lf,%lf\n", data->time[idx], data->voltage[idx], predictions[n]);
            }
            fclose(out_fp);
            printf("Wrote predictions to %s\n", out_filename);
        } else {
            printf("Error opening output file %s\n", out_filename);
        }
        
        // Free allocated memory.
        free(predictions);
        free(mu_history);
        for (int n = 0; n < num_iterations; n++) {
            free(w_hist[n]);
            free(error_hist[n]);
        }
        free(w_hist);
        free(error_hist);
        free(data->time);
        free(data->voltage);
        free(data);
    }
    
    return 0;
}
