using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class scene_manager : MonoBehaviour
{
    public void start_game()
    {
        game_manager.IsPaused = false;
        game_manager.Score = 0;
        SceneManager.LoadScene(1);
    }
}
