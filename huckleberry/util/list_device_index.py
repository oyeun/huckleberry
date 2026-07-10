import pyaudio

p = pyaudio.PyAudio()

# List all audio devices to find your hardware microphone
for i in range(p.get_device_count()):
  dev = p.get_device_info_by_index(i)
  print(f"Device Index {i}: {dev['name']} (Input Channels: {dev['maxInputChannels']})")
