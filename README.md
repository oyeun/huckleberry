# 🫐 Huckleberry.py

💬 _"Huckleberry, what is your purpose?"_

> 🫐: My purpose is simple - voice UX, but my use is versatile. I was written to run standalone on a Raspberry Pi as a voice assistant like Google Home or Amazon Alexa. I can also be used as a module within another project for voice control. Or I can be run on a PC or Mac to manage and test a Houndify client, which is what powers me.

Huckleberry is a Python project for voice control via the Houndify platform. It handles voice activation (wakeword), sending the voice query to Houndify, and response handling. On the Houndify side, your client analyzes the spoken query then, depending on the query or how the client is configured, returns a response containing the intent or desired content.

Functionality includes:

* runs in a thread and is non-blocking
* supports custom wakewords
* voice activity detection
* can be configured to be activated by wakeword (_"Hey Poodle"_), function call (`huckleberry.activate()`), or straight to command (_"What time is it?"_)
* plays audio alerts and spoken responses
* ability to input text commands or audio files containing voice commands (useful for testing)
* integration with the Houndify platform, which provides:
  * a wide variety of domains (weather, sports, wikipedia, home automation, etc.)
  * voice responses with different voice options
  * custom commands
* highly configurable

## Dependencies

This project relies on the Houndify platform which requires an account and an internet connection. You will probably need a microphone too!

- OS: Tested on Mac and Raspbian, should work with Windows but untested.
- Python >= 3.9

## Installation

First you will need to install some audio libraries on your machine.

MacOS:
```
brew install portaudio
```

GNU/Linux:
```
sudo apt install python3-pyaudio
```

Now you should be able to install the huckleberry package. From the project root directory, run:
```
pip install -e .
```

## Usage

```
# import Huckleberry and the config class
from huckleberry import Huckleberry
from huckleberry.config import HuckleberryConfig

# write and configure your response handler class - implement on_activate(), on_deactivate(), on_response(response), and close()
# see handler/houndify_handler.py for example
from myhandler import MyHandler

# configure Huckleberry, you can use a dict or instantiate the config class directly
# see config/config.py for configurations
dict_config = {...}

# instantiate your handler
handler = MyHandler(...)

# instantiate Huckleberry
huckleberry = Huckleberry(HuckleberryConfig(**dict_config), handler)

# start Huckleberry (non-blocking)
huckleberry.start()

# do your stuff. huckleberry is running in a thread and will be activated by wakeword, and your handler will process the response from Houndify

# to stop Huckleberry, call:
huckleberry.stop()
```

Write your own handler to handle responses and perform logic or route accordingly. See `/handler/houndify_handler.py` for reference, it is a simple handler that parses the response and outputs the voice response. 

## Sample Code

Check out the `examples` subdirectory for sample code.

Here is a demo of Huckleberry running on my Raspberry Pi 3:

https://github.com/user-attachments/assets/2ad86a31-038d-454f-886f-53ee7a64fc09

## Next Steps

- Clean up the code™
- Documentation
- More examples
- Create tools to manage Houndify custom commands
- Decouple Houndify from Huckleberry and add support for other voice platforms
- Create util script and possible module for LED management
- Package and upload to PyPi
