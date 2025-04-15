using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class teleport_enemy : MonoBehaviour
{
    [SerializeField] private Transform player;
    [SerializeField] private float teleportStepSize = 3f;
    [SerializeField] private float gameOverDistance = 1.5f;
    [SerializeField] private GameObject game_over;


    public void TeleportCloser()
    {
        Vector3 toGhost = transform.position - player.position;
        Vector3 toGhostDir = toGhost.normalized;

        // Get a random perpendicular vector in the horizontal plane
        Vector3 transverse = Vector3.Cross(toGhostDir, Vector3.up).normalized;

        // Randomly flip left or right
        if (Random.value > 0.5f) transverse = -transverse;

        // Add a little bit of forward motion (10-30% toward player)
        Vector3 forwardNudge = toGhostDir * -1f; // Toward player
        Vector3 moveDir = (transverse * 0.6f + forwardNudge * 0.4f).normalized;

        float randomStep = Random.Range(teleportStepSize * 0.5f, teleportStepSize * 1.2f);
        Vector3 step = moveDir * randomStep;
        if (Vector3.Distance(transform.position, player.position) < teleportStepSize)
        {
            step = forwardNudge * teleportStepSize * 0.5f;
        }
        step.y = 0f;
        transform.position += step;

        float newDist = Vector3.Distance(transform.position, player.position);
        if (newDist <= gameOverDistance)
        {
            Debug.Log("GAME OVER — The ghost caught you!");
            // Trigger game over
            game_over.SetActive(true);
            StartCoroutine(end_game());
        }
    }

    IEnumerator end_game()
    {
        yield return new WaitForSeconds(3f);
        SceneManager.LoadScene(1);
    }
}