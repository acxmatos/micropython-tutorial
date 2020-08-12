import machine
import network
import sys
import time
import urequests
import config


def connect_wifi():

    # Disables the access point interface (not used in this chapter)
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)

    # Configure station interface (wifi client)
    sta_if = network.WLAN(network.STA_IF)

    # Are we already connected?
    if not sta_if.isconnected():

        # Connect to the wifi network with settings coming from
        # config file (/pyboard/config.py)
        print('Connecting to WiFi...')
        sta_if.active(True)
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

        # Wait for the connection to be established
        # Note: the connect command issued above is asynchronous
        #       so the wait loop is needed to prevent the function
        #       from quiting before making sure we are for sure
        #       connected to the wifi
        while not sta_if.isconnected():
            time.sleep(1)  # wait another second

    # We are now connected! Print the network configuration
    print('Network config:', sta_if.ifconfig())


def call_webhook():

    # Call webhook to trigger the button_pressed event
    print('Invoking webhook')
    response = urequests.post(config.WEBHOOK_URL,
                              json={'value1': config.BUTTON_ID})

    # Any response code below 400 is considered success in this case
    if response is not None and response.status_code < 400:
        print('Webhook invoked')
    else:
        print('Webhook failed')
        raise RuntimeError('Webhook failed')


def show_error():

    # LEDs setup
    led_top = machine.Pin(config.LED_TOP_PIN, machine.Pin.OUT)
    led_bottom = machine.Pin(config.LED_BOTTOM_PIN, machine.Pin.OUT)

    # Blink 3 times to show error
    for i in range(3):
        led_top.on()
        led_bottom.off()
        time.sleep(0.5)
        led_top.off()
        led_bottom.on()
        time.sleep(0.5)

    # Turn off both LEDs
    led_top.on()
    led_bottom.on()


def is_debug():
    debug = machine.Pin(config.DEBUG_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    if debug.value() == 0:
        print('Debug mode detected.')
        return True
    return False


def run():

    # machine.PWRON_RESET: the device was just powered on for the first time.
    # machine.HARD_RESET: the device is coming back from a "hard" reset,
    #                     such as when pressing the reset button.
    # machine.WDT_RESET: the watchdog timer reset the device. This is a mechanism
    #                    that ensures the device is reset if it crashes or hangs.
    # machine.DEEPSLEEP_RESET: the device was reset while being in deep sleep mode.
    # machine.SOFT_RESET: the device is coming back from a "soft" reset, such as
    #                     when pressing Ctrl-D when in the REPL.

    try:
        # Notify via webhook only when the device is coming
        # back from a deep sleep mode
        if machine.reset_cause() == machine.DEEPSLEEP_RESET:
            connect_wifi()
            call_webhook()
    except Exception as exc:
        sys.print_exception(exc)
        show_error()

    # Enter in deep sleep mode only if not in debug
    if not is_debug():
        machine.deepsleep()


run()
