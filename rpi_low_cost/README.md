# Installation
First you need to install circuit python on your Raspberry Pi Pico. You can do so here at this link: https://circuitpython.org/board/raspberry_pi_pico_w/

# Uploading our code to you Pico
Next you need to upload our code.py into your circuitpy drive that was created from installing circuit python onto your Pico. Afterwards you need to edit/create a settings.toml where you need to include some information.
You need the following information in your settings.toml 'CIRCUITPY_WIFI_SSID', 'CIRCUITPY_WIFI_PASSWORD', 'CIRCUITPY_MULTICAST_GROUP', 'CIRCUITPY_PORT', 'CIRCUITPY_RATE'.

# Using the code
Once you upload the code to the Pico you should be good to go. Now whenever you power the Pico it should create a wifi network with the name and password you specified in the settings.toml.
Once you connect to the wifi it should broadcast data to the ip specified in your mulitcast group and at the port specified in the settings.toml.
