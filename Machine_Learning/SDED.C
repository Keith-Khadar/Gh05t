#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>  // Include for timing

#define M 10

// --------------------------------------------------------------------
// SDES Functions (converted from Python)
// --------------------------------------------------------------------

// Computes the new effective DC value, the measurement (absolute difference),
// and sets spike to 1 if the measurement exceeds delta, else 0.
void apply_sded(double x, double eff_dc, double alpha, double delta, 
                double *new_eff_dc, double *meas, int *spike) {
    *new_eff_dc = alpha * x + (1.0 - alpha) * eff_dc;
    *meas = fabs(x - *new_eff_dc);
    *spike = (*meas > delta) ? 1 : 0;
}

// Processes an array x of length n. For each element (starting at index 1),
// it computes a new effective DC value, a measurement, and a spike flag.
// The arrays eff_dc, measures, and spikes must be preallocated (length n).
void apply_sded_full(const double *x, int n, double alpha, double delta,
                     double *eff_dc, double *measures, int *spikes) {
    // Initialize the first element
    eff_dc[0] = 0.0;
    measures[0] = 0.0;
    spikes[0] = 0;

    // Timing variables
    clock_t start, end;
    double total_time = 0.0;

    // Loop over the rest of the array
    for (int i = 1; i < n; i++) {
        start = clock();  // Start timing
        apply_sded(x[i], eff_dc[i-1], alpha, delta, &eff_dc[i], &measures[i], &spikes[i]);
        end = clock();    // End timing

        // Compute elapsed time for this iteration
        double elapsed = ((double)(end - start)) / CLOCKS_PER_SEC;
        total_time += elapsed;
    }

    // Compute average time per iteration
    double avg_time = total_time / (n - 1);
    
    // Log the result
    FILE *log_fp = fopen("performance_log.txt", "a");  // Open log file in append mode
    if (log_fp) {
        fprintf(log_fp, "Processed %d iterations. Average time per apply_sded: %f seconds\n", n - 1, avg_time);
        fclose(log_fp);
    }
}

// --------------------------------------------------------------------
// CSV Loading
// --------------------------------------------------------------------

// A structure to hold our CSV data (only Time and Channel1)
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

// --------------------------------------------------------------------
// Main Program
// --------------------------------------------------------------------
int main() {
    // Compute the filter as in Python.
    // (Even though it is not used later, we include it for completeness.)
    double filter[M];
    for (int i = 0; i < M; i++) {
        filter[i] = -1.0 / sqrt((double) M);
    }
    double applied_filter = 0.0;
    double scale = 1.2;
    double deviation = 0.005477277382981891;  // Empirically determined standard deviation threshold
    double threshold = scale * deviation;       // Threshold for spike detection
    double alpha = 0.005;
    
    double avg_std = 0.0; // Not used further in this example.
    
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
        
        // Allocate arrays for SDES outputs.
        double *eff_dc   = (double*) calloc(N, sizeof(double));
        double *measures = (double*) calloc(N, sizeof(double));
        int    *spikes   = (int*)    calloc(N, sizeof(int));
        
        // Apply the SDES filter to the voltage data.
        apply_sded_full(data->voltage, N, alpha, threshold, eff_dc, measures, spikes);
        
        // In Python you plotted the results.
        // Here, we output the time, DC-removed signal (measures), and spike train
        // to a CSV file (e.g., output0.csv) for external plotting.
        char out_filename[256];
        sprintf(out_filename, "output%d.csv", i);
        FILE *out_fp = fopen(out_filename, "w");
        if (!out_fp) {
            printf("Error opening output file %s\n", out_filename);
        } else {
            // Write header.
            fprintf(out_fp, "Time,DC_Removed,Spike\n");
            for (int j = 0; j < N; j++) {
                fprintf(out_fp, "%lf,%lf,%d\n", data->time[j], measures[j], spikes[j]);
            }
            fclose(out_fp);
            printf("Processed %s and wrote results to %s\n", filename, out_filename);
        }
        
        // Free allocated memory.
        free(data->time);
        free(data->voltage);
        free(data);
        free(eff_dc);
        free(measures);
        free(spikes);
    }
    
    return 0;
}
