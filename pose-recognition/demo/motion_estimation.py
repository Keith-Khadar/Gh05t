import numpy as np
import json

# Load JSON data
with open("outputs/results_webcam.json", "r") as f:
    data = json.load(f)  # JSON file with keypoints per frame

frames = data['instance_info']  # Access the list of frames
time_interval = 1 / 30  # Assuming 30 FPS

# Define keypoint indices based on provided metadata
indices = {
    'left_shoulder': 5, 'right_shoulder': 6,
    'left_elbow': 7, 'right_elbow': 8,
    'left_wrist': 9, 'right_wrist': 10,
    'left_hip': 11, 'right_hip': 12,
    'left_knee': 13, 'right_knee': 14,
    'left_ankle': 15, 'right_ankle': 16,
    'left_foot': [17, 18],  # Use average of big toe and small toe
    'right_foot': [20, 21]
}

# Function to compute mean keypoint for feet
def mean_keypoint(frame, keypoint_indices):
    return np.mean([frame[i] for i in keypoint_indices], axis=0)

# Initialize storage for velocities and accelerations
results = {segment: {'velocities': [], 'accelerations': []} for segment in [
    'shoulder_elbow', 'elbow_wrist', 'shoulder_wrist',
    'hip_knee', 'knee_ankle', 'hip_ankle',
    'ankle_foot'
]}

# Process frames for velocities and accelerations
for t in range(len(frames) - 1):
    instances_t = frames[t]['instances']
    instances_t1 = frames[t + 1]['instances']

    if not instances_t or not instances_t1:
        continue  # Skip frames with no instances

    frame_t = np.array(instances_t[0]['keypoints'])  # Current frame
    frame_t1 = np.array(instances_t1[0]['keypoints'])  # Next frame

    for side in ['left', 'right']:
        # Extract keypoints at time t
        shoulder_t = frame_t[indices[f'{side}_shoulder']]
        elbow_t = frame_t[indices[f'{side}_elbow']]
        wrist_t = frame_t[indices[f'{side}_wrist']]
        hip_t = frame_t[indices[f'{side}_hip']]
        knee_t = frame_t[indices[f'{side}_knee']]
        ankle_t = frame_t[indices[f'{side}_ankle']]
        foot_t = mean_keypoint(frame_t, indices[f'{side}_foot'])

        # Extract keypoints at time t+1
        shoulder_t1 = frame_t1[indices[f'{side}_shoulder']]
        elbow_t1 = frame_t1[indices[f'{side}_elbow']]
        wrist_t1 = frame_t1[indices[f'{side}_wrist']]
        hip_t1 = frame_t1[indices[f'{side}_hip']]
        knee_t1 = frame_t1[indices[f'{side}_knee']]
        ankle_t1 = frame_t1[indices[f'{side}_ankle']]
        foot_t1 = mean_keypoint(frame_t1, indices[f'{side}_foot'])

        # Compute segments at time t
        segments_t = {
            'shoulder_elbow': elbow_t - shoulder_t,
            'elbow_wrist': wrist_t - elbow_t,
            'shoulder_wrist': wrist_t - shoulder_t,
            'hip_knee': knee_t - hip_t,
            'knee_ankle': ankle_t - knee_t,
            'hip_ankle': ankle_t - hip_t,
            'ankle_foot': foot_t - ankle_t
        }

        # Compute segments at time t+1
        segments_t1 = {
            'shoulder_elbow': elbow_t1 - shoulder_t1,
            'elbow_wrist': wrist_t1 - elbow_t1,
            'shoulder_wrist': wrist_t1 - shoulder_t1,
            'hip_knee': knee_t1 - hip_t1,
            'knee_ankle': ankle_t1 - knee_t1,
            'hip_ankle': ankle_t1 - hip_t1,
            'ankle_foot': foot_t1 - ankle_t1
        }

        # Compute delta segments (difference between segments at t+1 and t)
        delta_segments = {segment: segments_t1[segment] - segments_t[segment] for segment in segments_t}

        # Compute velocities
        velocities = {segment: delta_segments[segment] / time_interval for segment in delta_segments}

        # Append velocities to results
        for segment, velocity in velocities.items():
            results[segment]['velocities'].append(velocity.tolist())

# Compute accelerations (finite differences of velocities)
for segment in results:
    velocities = np.array(results[segment]['velocities'])
    accelerations = np.diff(velocities, axis=0) / time_interval
    results[segment]['accelerations'] = accelerations.tolist()

# Save results to JSON
with open("outputs/moments.json", "w") as f:
    json.dump(results, f, indent=4)

print("Velocities and accelerations saved to results.json")