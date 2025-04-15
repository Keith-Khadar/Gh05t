using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;

public class websocket_connection : MonoBehaviour
{
    public TMP_InputField text;

    private void Start()
    {
        text.text = ip_address.URL;
    }
    public void Connect()
    {
        print(text.text);
        ip_address.URL = text.text;
        SceneManager.LoadScene(1);
    }
}
