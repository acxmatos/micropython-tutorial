# Core
import sys
import time
import machine

# Network
import network
import urequests

# Sensors/Displays
import dht
import sh1106
import framebuf

# Config
import config

# Custom Fonts
import freesans20
import writer


# -------------------------------------------------------------------------------------
#                                  Network Handling
# -------------------------------------------------------------------------------------


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


# -------------------------------------------------------------------------------------
#                          Feedback / Visual Status Reports
# -------------------------------------------------------------------------------------


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


# -------------------------------------------------------------------------------------
#                              Execution Flow Control
# -------------------------------------------------------------------------------------


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


# -------------------------------------------------------------------------------------
#                         Temperature and Humidity Handling
#                                  DHT22 = measure
#                               OLED SH1106 = display
# -------------------------------------------------------------------------------------


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


def display_temperature_and_humidity(temperature, humidity):

    # Initialize I2C interface using the setup display pins
    i2c = machine.I2C(scl=machine.Pin(config.DISPLAY_SCL_PIN),
                      sda=machine.Pin(config.DISPLAY_SDA_PIN),
                      freq=400000)

    # Display detected?
    if 60 not in i2c.scan():
        print('Cannot find display')
        raise RuntimeError('Cannot find display')

    # For SSD1306 OLED Display
    # display = ssd1306.SSD1306_I2C(128, 64, i2c)

    # For SH1106 OLED Display
    display = sh1106.SH1106_I2C(128, 64, i2c, machine.Pin(16), 0x3c)

    # Custom font writer
    font_writer = writer.Writer(display, freesans20)

    # Load PBM images
    temperature_pbm = load_image('temperature.pbm')
    units_pbm = load_image(
        'fahrenheit.pbm' if config.FAHRENHEIT else 'celsius.pbm')
    humidity_pbm = load_image('humidity.pbm')
    percent_pbm = load_image('percent.pbm')

    # Clean display content
    display.fill(0)

    # -------- V0 --------

    # Prepare text information using 16 pixels per line x 4 lines
    # Use formating ({:^16s}) to center text

    # Temperature (lines 1 & 2)
    # display.text('{:^16s}'.format('Temperature:'), 0, 0)
    # display.text('{:^16s}'.format(str(temperature) +
    #                              ('F' if config.FAHRENHEIT else 'C')), 0, 16)
    # Humidity (lines 3 & 4)
    # display.text('{:^16s}'.format('Humidity:'), 0, 32)
    # display.text('{:^16s}'.format(str(humidity) + '%'), 0, 48)

    # -------- V1 --------

    # Draw a rectangle along the display borders
    display.rect(0, 0, 128, 64, 1)

    # Draw a line in the middle to separate things
    display.line(64, 0, 64, 64, 1)

    # Draw temperature symbol
    display.blit(temperature_pbm, 24, 4)

    # Draw humidity symbol
    display.blit(humidity_pbm, 88, 4)

    # Draw units symbol
    display.blit(units_pbm, 28, 52)

    # Draw percent symbol
    display.blit(percent_pbm, 92, 52)

    # Format current temperature using custom fonts
    text = '{:.1f}'.format(temperature)
    textlen = font_writer.stringlen(text)
    font_writer.set_textpos((64 - textlen) // 2, 30)
    font_writer.printstring(text)

    # Format current humidity using custom fonts
    text = '{:.1f}'.format(humidity)
    textlen = font_writer.stringlen(text)
    font_writer.set_textpos(64 + (64 - textlen) // 2, 30)
    font_writer.printstring(text)

    # Show content
    display.rotate(config.DISPLAY_ROTATE)
    display.show()

    # Wait 10 seconds
    time.sleep(10)

    # Power off display
    display.poweroff()


def load_image(filename):

    # Open PBM file
    with open(filename, 'rb') as f:

        # Ignore first two lines (format and description, not important)
        f.readline()
        f.readline()

        # Read image width and height
        width, height = [int(v) for v in f.readline().split()]

        # Read image data
        data = bytearray(f.read())

    # Return image in a FrameBuffer HLSB format
    #
    # framebuf.MONO_HLSB: Monochrome (1-bit) color format This defines a
    # mapping where the bits in a byte are horizontally mapped. Each byte
    # occupies 8 horizontal pixels with bit 0 being the leftmost. Subsequent
    # bytes appear at successive horizontal locations until the rightmost
    # edge is reached. Further bytes are rendered on the next row, one pixel
    # lower.
    return framebuf.FrameBuffer(data, width, height, framebuf.MONO_HLSB)

# -------------------------------------------------------------------------------------
#                                 Run Logic
# -------------------------------------------------------------------------------------


def run_cycle():

    try:
        # Connect to internet through wifi
        connect_wifi()

        # Collect current temperature and humidity information
        temperature, humidity = get_temperature_and_humidity()

        # Display temperature and humidity information
        display_temperature_and_humidity(temperature, humidity)

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
        while(not is_debug()):

            # Run single cycle
            run_cycle()

            # Enter in sleep mode only if not in debug
            time.sleep(config.LOG_INTERVAL)


# -------------------------------------------------------------------------------------
#                                 Main Execution
# -------------------------------------------------------------------------------------

# Run the program
run()
