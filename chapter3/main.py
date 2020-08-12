import machine
import time

LED_TOP_PIN = 2  # D4
LED_BOTTOM_PIN = 16  # D0
BUTTON_PIN = 14  # D5


def blink():

    # Board top LED (D4)
    led = machine.Pin(LED_TOP_PIN, machine.Pin.OUT)

    # Board bottom LED (D0)
    led2 = machine.Pin(LED_BOTTOM_PIN, machine.Pin.OUT)

    # Button (D5) with pull-up resistor enabled
    button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

    # Blink LEDs while the button is NOT pressed
    # Reminder: button is reversed wired to the board, so
    #           pressing it will result in LOW value and
    #           releasing it will result in HIGH value.
    #           We will repeat while value is in HIGH,
    #           meaning button released
    while button.value():
        led.on()
        led2.off()
        time.sleep(0.5)
        led.off()
        led2.on()
        time.sleep(0.5)

    # Turn LEDs off when button is pressed
    # Reminder: LEDs are reversed wired to the board, so
    #           on (HIGH) will turn it off and off (LOW)
    #           will turn it on
    led.on()
    led2.on()


blink()
