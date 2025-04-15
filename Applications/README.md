# NuGet for Unity - WebSocketSharp Installation Guide

## Installation Steps

1. Install NuGet for Unity by following the guide at https://github.com/GlitchEnzo/NuGetForUnity
2. Restart Unity
3. Click on the NuGet tab and select "Manage Packages"
4. Search for and install WebSocketSharp-netstandard

## Example Usage

```csharp
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using WebSocketSharp;

public class WebSocketConnection : MonoBehaviour
{
    [System.Serializable]
    public class LabelMessage
    {
        public int label;
    }
    
    WebSocket ws;
    
    private void Start()
    {
        ws = new WebSocket("ws://10.78.4.19:4242");
        ws.Connect();
        ws.OnMessage += (sender, e) =>
        {
            BlinkDetector.Blink = (JsonUtility.FromJson<LabelMessage>(e.Data).label == 1);
        };
    }
}
```
