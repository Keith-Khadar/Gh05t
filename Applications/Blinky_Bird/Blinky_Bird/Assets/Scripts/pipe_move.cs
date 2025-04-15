using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class pipe_move : MonoBehaviour
{
    public float moveSpeed = 5f;

    void Update()
    {
        if (!game_manager.IsPaused)
        {
            transform.position += Vector3.left * moveSpeed * Time.deltaTime;
        }
    }

    private void OnTriggerEnter2D(Collider2D collision)
    {
        if(collision.tag == "End")
        {
            Destroy(gameObject);
        }
    }
}
