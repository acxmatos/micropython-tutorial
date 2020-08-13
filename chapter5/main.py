import dht
import machine
import network
import sys
import time
import urequests
import config


def connect_wifi():

    print('Setting up wifi connection')

    # Disables the access point interface (not used in this chapter)
    print('Disabling access point interface')
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)

    # Configure station interface (wifi client)
    sta_if = network.WLAN(network.STA_IF)

    # Are we already connected?
    if not sta_if.isconnected():

        print('Station interface not connected. Establishing connection')

        # Connect to the wifi network with settings coming from
        # config file (/pyboard/config.py)
        sta_if.active(True)
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

        # Wait for the connection to be established
        # Note: the connect command issued above is asynchronous
        #       so the wait loop is needed to prevent the function
        #       from quiting before making sure we are for sure
        #       connected to the wifi
        while not sta_if.isconnected():

            print('Waiting 1 second for the connection to be established')
            show_wifi_connect_wait()
            time.sleep(1)  # wait another second

    # We are now connected! Print the network configuration
    print('Connection successful!')
    print('Network config:', sta_if.ifconfig())
    show_wifi_connect_success()


def blink_led(delay, times=1):

    # LED setup (only top LED, as the bottom LED is powered by
    # D0, which in this program is used by the alarm to wake
    # the machine up from deep sleep)
    led_top = machine.Pin(config.LED_TOP_PIN, machine.Pin.OUT)

    # Blink "n" times with delay
    for i in range(times):
        led_top.on()
        time.sleep(delay)
        led_top.off()
        time.sleep(delay)

    led_top.on()


def show_wifi_connect_wait():

    # Blink 1 time (quick) to show progress
    blink_led(delay=0.05)


def show_wifi_connect_success():

    # Blink 3 times (quick) to show success
    blink_led(delay=0.05, times=3)


def show_success():

    # Blink 1 time (slow) to show success
    blink_led(delay=0.5)


def show_error():

    # Blink 3 times (slow) to show error
    blink_led(delay=0.5, times=3)


def is_debug():
    
    # Read debug pin
    debug = machine.Pin(config.DEBUG_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    
    # Check if debug pin is set to GND
    if debug.value() == 0:
        print('Debug mode enabled')
        return True

    print('Debug mode disabled')
    return False


def deepsleep():

    print('Going into deepsleep for {seconds} seconds...'.format(
        seconds=config.LOG_INTERVAL))

    # RTC = Real Time Clock
    rtc = machine.RTC()

    # Setup the machine to wake up from a deep sleep mode when the alarm goes off
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)

    # Set the alarm to go off within the setup interval
    rtc.alarm(rtc.ALARM0, config.LOG_INTERVAL * 1000)

    # Enters deep sleep mode
    machine.deepsleep()


def get_temperature_and_humidity():

    # DHT22 sensor setup
    dht22 = dht.DHT22(machine.Pin(config.DHT22_PIN))

    # Run measure
    print('Measuring temperature and humidity through DHT22')
    dht22.measure()

    # Get humidity measured
    humidity = dht22.humidity()

    # Get temperature measured
    temperature = dht22.temperature()

    # Convert to Fahrenheit if set to do so
    if config.FAHRENHEIT:
        print('Converting to Fahrenheit')
        temperature = temperature * 9 / 5 + 32

    print('Measures: temperature = {temperature}, humidity = {humidity}'.format(
          temperature=temperature, humidity=humidity))

    # Returns temperature (converted or not) and humidity
    return temperature, humidity


def log_data(temperature, humidity):

    # Call webhook to log the current temperature and humidity
    print('Uploading measured data to cloud')
    url = config.WEBHOOK_URL.format(temperature=temperature, humidity=humidity)
    response = urequests.get(url)

    # Any response code below 400 is considered success in this case
    if response.status_code < 400:
        print('Upload successful!')
        show_success()
    else:
        print('Upload failed!')
        raise RuntimeError('Upload failed!')


def run_cycle():

    try:
        # Connect to internet through wifi
        connect_wifi()

        # Collect current temperature and humidity information
        temperature, humidity = get_temperature_and_humidity()

        # Log current temperature and humidity to cloud service
        log_data(temperature, humidity)

    except Exception as exc:
        sys.print_exception(exc)
        show_error()


def run():

    if config.DEEP_SLEEP:

        print('Running in DEEP_SLEEP mode')

        # Run single cycle
        run_cycle()

        # Enter in deep sleep mode only if not in debug
        if not is_debug():
            deepsleep()

    else:

        print('Running in endless loop')

        # Run forever
        while(True):

            # Run single cycle
            run_cycle()

            # Sleep for the ammount of configured time
            time.sleep(config.LOG_INTERVAL)


# Run the program
run()
