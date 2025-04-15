using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class game_manager
{
    private static int _score = 0;
    private static int _highscore = 0;
    private static bool _isPaused = false;
    public static int Score
    {
        get => _score;
        set => _score = Mathf.Max(0, value); // Prevent negative score
    }
    public static int Highscore
    {
        get => _highscore;
        set => _highscore = Mathf.Max(0, value); // Prevent negative score
    }

    public static bool IsPaused
    {
        get => _isPaused;
        set
        {
            _isPaused = value;
            Time.timeScale = _isPaused ? 0f : 1f; // Actually pause the game
        }
    }

    public static void AddScore(int amount)
    {
        Score += amount;
        Highscore = Mathf.Max(Highscore, Score);
    }

    public static void ResetGame()
    {
        _score = 0;
        IsPaused = false;
    }

    public static void TogglePause()
    {
        IsPaused = !IsPaused;
    }
}
