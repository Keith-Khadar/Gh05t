using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using WebSocketSharp;


[System.Serializable]
public class LabelMessage
{
    public int label;
}

public class player_controller : MonoBehaviour
{
    Rigidbody2D rb;
    public float upforce = 1f;
    bool isJumping = false;
    public TextMeshProUGUI score;
    public GameObject GameOver;

    WebSocket ws;
    bool blink = false;

    private void Start()
    {
        ws = new WebSocket(ip_address.URL);
        ws.Connect();
        ws.OnMessage += (sender, e) =>
        {
            blink = (JsonUtility.FromJson<LabelMessage>(e.Data).label == 1);
        };
    }

    void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    // Update is called once per frame
    void Update()
    {

        if (!isJumping && (blink || Input.GetKeyDown(KeyCode.Space) || Input.GetKeyDown(KeyCode.W) || Input.GetKeyDown(KeyCode.UpArrow)))
        {
            isJumping = true;
            rb.AddForce(Vector2.up * upforce);
            StartCoroutine(jump_cooldown());
        }
    }


    private IEnumerator jump_cooldown()
    {
        yield return new WaitForSeconds(0.1f);
        isJumping = false;
    }

    private void OnTriggerEnter2D(Collider2D collision)
    {
        if (collision.tag == "Obstacle")
        {
            game_manager.AddScore(1);
            score.text = "Score: " + game_manager.Score;
        }
    }
    private void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.collider.tag == "Obstacle")
        {
            isJumping = true;
            GameOver.SetActive(true);
            print("you died :(");
            StartCoroutine(resetGame());
        }
    }

    IEnumerator resetGame()
    {
        yield return new WaitForSeconds(5f);
        SceneManager.LoadScene(0);
    }
}