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
// NLMS Filter Functions
// ------------------------------

// This function applies the NLMS filter for one sample.
// x_in: pointer to input vector (length M)
// w: pointer to current filter weights (length M)
// y_noisy: desired (noisy) output (scalar)
// M: filter order
// mu: learning rate
// eps: regularization parameter
// Outputs:
//   *y_hat: computed filter output
//   w_new: updated filter weights (length M)
//   *mu_eff: effective learning rate for this sample
//   *e: estimation error (desired - output)
void apply_nlms_filter(const double *x_in, const double *w, double y_noisy, int M,
                       double mu, double eps, double *y_hat, double *w_new,
                       double *mu_eff, double *e) {
    double dot = 0.0;
    double x_pow = 0.0;
    for (int i = 0; i < M; i++) {
        dot += w[i] * x_in[i];
        x_pow += x_in[i] * x_in[i];
    }
    *y_hat = dot;
    *e = y_noisy - dot;
    *mu_eff = mu / (x_pow + eps);
    for (int i = 0; i < M; i++) {
        w_new[i] = w[i] + (*mu_eff) * (*e) * x_in[i];
    }
}

// Applies the NLMS filter over the full input sequence.
// x_in: input signal (length N)
// d: desired signal (length N)
// N: number of samples
// M: filter order
// mu: learning rate, eps: regularization parameter
// y_hat: output prediction array (length N)
// e_hist: error history (length N)
// mu_eff_hist: effective mu history (length N)
// w_hist: 2D array to store filter weight history for each iteration (N x M)
void nlms_filter_full(const double *x_in, const double *d, int N, int M,
                      double mu, double eps, double *y_hat, double *e_hist,
                      double *mu_eff_hist, double **w_hist) {
    // Create a padded input array: pad with M zeros at the beginning.
    // In Python: x_eff = pad(x_in, (M, 0)) then drop the last sample.
    // Here, we allocate (N + M) samples and use indices 0 to N+M-2.
    int padded_length = N + M;
    double *x_eff = (double *) malloc(padded_length * sizeof(double));
    // Fill first M elements with 0.
    for (int i = 0; i < M; i++) {
        x_eff[i] = 0.0;
    }
    // Copy x_in into x_eff starting at index M.
    for (int i = 0; i < N; i++) {
        x_eff[i + M] = x_in[i];
    }
    // We will use x_eff[0] to x_eff[N+M-2] so that for each n from 0 to N-1,
    // the vector x_eff[n] ... x_eff[n+M-1] has length M.

    // Initialize filter weights (w) to zeros.
    double *w = (double *) calloc(M, sizeof(double));
    // Temporary array to hold updated weights.
    double *w_new = (double *) malloc(M * sizeof(double));

    for (int n = 0; n < N; n++) {
        double *x_vec = &x_eff[n];  // current input vector of length M
        double current_y_hat, current_mu_eff, current_e;
        // Apply NLMS update.
        apply_nlms_filter(x_vec, w, d[n], M, mu, eps,
                          &current_y_hat, w_new, &current_mu_eff, &current_e);
        y_hat[n] = current_y_hat;
        e_hist[n] = current_e;
        mu_eff_hist[n] = current_mu_eff;
        // Save the current filter weights into history.
        if (w_hist != NULL) {
            for (int i = 0; i < M; i++) {
                w_hist[n][i] = w_new[i];
            }
        }
        // Update weights for the next iteration.
        for (int i = 0; i < M; i++) {
            w[i] = w_new[i];
        }
    }
    free(w);
    free(w_new);
    free(x_eff);
}

// ------------------------------
// Main Program
// ------------------------------
int main() {
    int M = 4;            // Filter order
    double mu = 0.1;      // Learning rate
    double eps = 1e-15;   // Regularization parameter

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
        
        // For this NLMS filter, we use the voltage as both the input and desired signal.
        // Allocate memory for outputs.
        double *y_hat   = (double *) malloc(N * sizeof(double));
        double *e_hist  = (double *) malloc(N * sizeof(double));
        double *mu_eff_hist = (double *) malloc(N * sizeof(double));
        
        // Allocate memory for weight history (optional).
        double **w_hist = (double **) malloc(N * sizeof(double *));
        for (int n = 0; n < N; n++) {
            w_hist[n] = (double *) malloc(M * sizeof(double));
        }
        
        // Apply the NLMS filter.
        nlms_filter_full(data->voltage, data->voltage, N, M, mu, eps,
                         y_hat, e_hist, mu_eff_hist, w_hist);
        
        // Compute NMSE: norm(e_hist) / norm(voltage)
        double norm_e = 0.0;
        double norm_volt = 0.0;
        for (int j = 0; j < N; j++) {
            norm_e += e_hist[j] * e_hist[j];
            norm_volt += data->voltage[j] * data->voltage[j];
        }
        norm_e = sqrt(norm_e);
        norm_volt = sqrt(norm_volt);
        double nmse = norm_e / norm_volt;
        printf("File %s, NMSE: %lf\n", filename, nmse);
        
        // Write the predictions to a CSV file (e.g., output0.csv) for external plotting.
        char out_filename[256];
        sprintf(out_filename, "output%d.csv", i);
        FILE *out_fp = fopen(out_filename, "w");
        if (out_fp) {
            // Write header.
            fprintf(out_fp, "Time,TrueVoltage,Prediction\n");
            for (int j = 0; j < N; j++) {
                fprintf(out_fp, "%lf,%lf,%lf\n", data->time[j], data->voltage[j], y_hat[j]);
            }
            fclose(out_fp);
            printf("Wrote predictions to %s\n", out_filename);
        } else {
            printf("Error opening output file %s\n", out_filename);
        }
        
        // Free allocated memory.
        free(y_hat);
        free(e_hist);
        free(mu_eff_hist);
        for (int n = 0; n < N; n++) {
            free(w_hist[n]);
        }
        free(w_hist);
        free(data->time);
        free(data->voltage);
        free(data);
    }
    
    return 0;
}
