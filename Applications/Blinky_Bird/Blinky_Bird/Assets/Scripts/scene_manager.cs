using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;
using TMPro;

public class scene_manager : MonoBehaviour
{
    public TMP_InputField inputField;
    public void start_game()
    {
        ip_address.URL = inputField.text;
        game_manager.IsPaused = false;
        game_manager.Score = 0;
        SceneManager.LoadScene(1);
    }
}
