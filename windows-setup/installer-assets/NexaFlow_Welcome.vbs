Option Explicit

Dim message

message = "Welcome to NexaFlow." & vbCrLf & vbCrLf & _
          "Your desktop automation workspace is ready. For the best first experience, " & _
          "we recommend reading the NexaFlow User Guide included with your download. " & _
          "It explains recording, playback, Focus Mode, hotkeys, safety options, and workflow management."

MsgBox message, vbInformation, "Welcome to NexaFlow"
