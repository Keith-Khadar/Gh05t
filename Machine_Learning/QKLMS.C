#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

// ------------------------------
// CSV Loading Functions & Data Structure
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
// QKLMS Functions
// ------------------------------

// Gaussian kernel for one-dimensional inputs.
double gaussian_kernel(double u, double v, double sigma) {
    return exp(-((u - v) * (u - v)) / (2 * sigma * sigma));
}

// Applies the QKLMS algorithm over an entire input sequence.
// u: Input signal array (e.g., voltage[0] to voltage[T-2]) of length n
// d: Desired output array (voltage[1] to voltage[T-1]) of length n
// eta: Step size (learning rate)
// sigma: Gaussian kernel width
// epsilon: Quantization threshold
//
// y_hat: Output prediction array (length n)
// codebook: Preallocated array to store centers (max size n)
// coeffs: Preallocated array for coefficients (max size n)
// codebook_count: Pointer to an int that will hold the final number of centers
void qklms_filter_full(const double *u, const double *d, int n, double eta, double sigma, double epsilon,
                       double *y_hat, double *codebook, double *coeffs, int *codebook_count) {
    int i, j;
    *codebook_count = 0;
    
    // Initialize the codebook with the first sample.
    codebook[0] = u[0];
    coeffs[0] = eta * d[0];
    *codebook_count = 1;
    y_hat[0] = coeffs[0] * gaussian_kernel(codebook[0], u[0], sigma);
    
    for (i = 1; i < n; i++) {
        double y = 0.0;
        // Compute filter output as a weighted sum over the current codebook.
        for (j = 0; j < *codebook_count; j++) {
            y += coeffs[j] * gaussian_kernel(codebook[j], u[i], sigma);
        }
        y_hat[i] = y;
        
        double e = d[i] - y;
        
        // Find the closest center in the codebook.
        double min_dist = fabs(u[i] - codebook[0]);
        int j_star = 0;
        for (j = 1; j < *codebook_count; j++) {
            double dist = fabs(u[i] - codebook[j]);
            if (dist < min_dist) {
                min_dist = dist;
                j_star = j;
            }
        }
        // If the distance is within the quantization threshold, update that center's coefficient.
        if (min_dist <= epsilon) {
            coeffs[j_star] += eta * e;
        } else {
            // Otherwise, add the new sample as a center.
            codebook[*codebook_count] = u[i];
            coeffs[*codebook_count] = eta * e;
            (*codebook_count)++;
        }
    }
}

// ------------------------------
// Main Program
// ------------------------------
int main() {
    // Process 10 files: eye_blinking0.csv to eye_blinking9.csv.
    for (int i = 0; i < 10; i++) {
        // Build the input filename.
        char filename[256];
        sprintf(filename, "eye_blinking%d.csv", i);
        
        // Load the CSV data.
        Data *data = load_csv(filename);
        if (data == NULL) {
            printf("Failed to load %s\n", filename);
            continue;
        }
        int N = data->n;
        if (N < 2) {
            printf("Not enough data in %s\n", filename);
            free(data->time);
            free(data->voltage);
            free(data);
            continue;
        }
        
        // For one-step-ahead prediction:
        // Input (u): voltage[0] to voltage[N-2]
        // Target (d): voltage[1] to voltage[N-1]
        int L = N - 1;
        double *u = (double*) malloc(L * sizeof(double));
        double *d = (double*) malloc(L * sizeof(double));
        for (int j = 0; j < L; j++) {
            u[j] = data->voltage[j];
            d[j] = data->voltage[j + 1];
        }
        
        // QKLMS parameters
        double eta = 0.1;      // Step size
        double sigma = 1.0;    // Gaussian kernel width
        double epsilon = 0.2;  // Quantization threshold
        
        // Allocate arrays for QKLMS outputs and the model.
        double *y_hat = (double*) malloc(L * sizeof(double));
        double *codebook = (double*) malloc(L * sizeof(double));  // Maximum possible centers = L
        double *coeffs = (double*) malloc(L * sizeof(double));
        int codebook_count = 0;
        
        // Apply QKLMS filter.
        qklms_filter_full(u, d, L, eta, sigma, epsilon, y_hat, codebook, coeffs, &codebook_count);
        
        printf("Processed file %s. Final number of centers: %d\n", filename, codebook_count);
        
        // Output the predictions to a CSV file (e.g., output0.csv) for external plotting.
        char out_filename[256];
        sprintf(out_filename, "output%d.csv", i);
        FILE *out_fp = fopen(out_filename, "w");
        if (out_fp) {
            // Write header.
            fprintf(out_fp, "Time,TrueVoltage,Prediction\n");
            // Note: target d corresponds to data->voltage[1] ... data->voltage[N-1],
            // and the corresponding time is data->time[1] ... data->time[N-1].
            for (int j = 0; j < L; j++) {
                fprintf(out_fp, "%lf,%lf,%lf\n", data->time[j + 1], d[j], y_hat[j]);
            }
            fclose(out_fp);
            printf("Wrote predictions to %s\n", out_filename);
        } else {
            printf("Error opening output file %s\n", out_filename);
        }
        
        // Free allocated memory.
        free(u);
        free(d);
        free(y_hat);
        free(codebook);
        free(coeffs);
        free(data->time);
        free(data->voltage);
        free(data);
    }
    
    return 0;
}
