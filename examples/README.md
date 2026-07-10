# Examples

## `bottled_huckleberry.py`

Bottled Huckleberry, control Huckleberry through a REST API.

### endpoints
| Method | Endpoint  | Action                                                                                                       |
|--------|-----------|--------------------------------------------------------------------------------------------------------------|
| GET    | /start    | Start Huckleberry - puts it in the wakeword state, awaiting user to say the wakeword to activate Huckleberry |
| GET    | /stop     | Stop Huckleberry - stops threads and closes processes for exit                                               |
| GET    | /activate | Activate Huckleberry - puts it in the activated state, actively sending audio input to Houndify              |
| POST   | /text     | Send a text command to Huckleberry                                                                           |
| POST   | /wav      | Send a pre-recorded command to Huckleberry. audio must contain wakeword and should be wav format             |
| GET    | /status   | Return Huckleberry status                                                                                    |

## `oypi_handler.py`

I used this handler for the video, it manages the LED lights on my Raspberry Pi's microphone array hat when Huckleberry is activated or deativated.

## Tips

- To skip the wakeword and just speak a command to activate Huckleberry, set the config `activation_method='vad'`. A few things to keep in mind:
  - The voice response will likely trigger Huckleberry. To avoid this, set the config `blocking_voice=True` so the response audio will block until it finishes playing.
  - Alternatively, use headphones.
  - Calibrate the `sensitivity` config if your environment is noisy.
- You can also programmatically activate Huckleberry with the `activate_hound()` method, if you want to trigger it with a button, for example.  