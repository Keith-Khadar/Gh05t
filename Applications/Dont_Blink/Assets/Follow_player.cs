using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using WebSocketSharp;
public class Follow_player : MonoBehaviour
{

    [SerializeField] private Transform player;
    private teleport_enemy teleport_script;
    [SerializeField] private float teleportInterval = 2f;
    public bool shouldTeleport = false;
    [SerializeField] private float lookThresholdAngle = 60f; // Ghost moves if outside this cone

    WebSocket ws;
    bool blink = false;

    [System.Serializable]
    public class LabelMessage
    {
        public int label;
    }

    private void Start()
    {
        teleport_script = GetComponent<teleport_enemy>();
        StartCoroutine(TeleportRoutine());
        ws = new WebSocket(ip_address.URL);
        ws.Connect();
        ws.OnMessage += (sender, e) =>
        {
            blink = (JsonUtility.FromJson<LabelMessage>(e.Data).label == 1);
            print(blink);
        };
    }

    // Update is called once per frame
    void Update()
    {
        // Always face the player
        if (player != null)
        {
            Vector3 direction = (player.position - transform.position).normalized;
            direction.y = 0f; // Keep enemy upright if needed
            transform.forward = direction;
        }
    }

    private IEnumerator TeleportRoutine()
    {
        while (true)
        {
            yield return new WaitForSeconds(teleportInterval);
            Vector3 toGhost = (transform.position - player.position).normalized;
            float angle = Vector3.Angle(player.forward, toGhost);
            if (angle > lookThresholdAngle || blink)
            {
                print("Teleporting");
                teleport_script.TeleportCloser();
            }
        }
    }
}
