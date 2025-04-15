using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class spawn_pipes : MonoBehaviour
{
    public GameObject pipe;
    public float minInterval = 0.5f;           // Fastest it can get
    public float maxInterval = 3.0f;           // Slowest at the start
    public float growthRate = 0.1f;            // How quickly it ramps up
    public float randomVariance = 0.3f;        // Amount of randomness (+/- seconds)

    private float timeSinceStart = 0f;
    private float timeSinceLastSpawn = 0f;

    public float minY = -3f;                 // Minimum height
    public float maxY = 3f;                  // Maximum height

    public float maxStep = 1.0f; // Max vertical change per step (for random walk)
    private float lastY = 0f;

    private void Start()
    {
        lastY = Random.Range(minY, maxY);
    }


    void Update()
    {
        timeSinceStart += Time.deltaTime;
        timeSinceLastSpawn += Time.deltaTime;

        // Exponentially decreasing interval
        float baseInterval = minInterval + (maxInterval - minInterval) * Mathf.Exp(-growthRate * timeSinceStart);

        // Add some randomness
        float randomOffset = Random.Range(-randomVariance, randomVariance);
        float actualInterval = Mathf.Max(minInterval, baseInterval + randomOffset);

        if (timeSinceLastSpawn >= actualInterval)
        {
            SpawnObstacle();
            timeSinceLastSpawn = 0f;
        }
    }

    void SpawnObstacle()
    {
        // Apply random walk from last Y
        float step = Random.Range(-maxStep, maxStep);
        float newY = Mathf.Clamp(lastY + step, minY, maxY);

        Vector3 spawnPos = new Vector3(transform.position.x, newY, 0f);

        Instantiate(pipe, spawnPos, Quaternion.identity);

        lastY = newY; // Update for next step
    }
}
