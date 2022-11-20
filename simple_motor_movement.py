import RPi.GPIO as GPIO
import time
from tqdm.auto import tqdm


def motor_single_step(_step_pin, _velocity):
    # This function makes the motor moves a single step in a defined time interval
    GPIO.output(_step_pin, GPIO.HIGH)
    time.sleep(0.5 * (1 / _velocity))
    GPIO.output(_step_pin, GPIO.LOW)
    time.sleep(0.5 * (1 / _velocity))


if __name__ == "__main__":
    # 0/1 used to define clockwise or counterclockwise.
    CW = 1
    CCW = 0
    directions = {'up': CW, 'down': CCW, 'left': CW, 'right': CCW, 'forward': CW, 'backward': CCW}

    a = 'x'

    axis = {'x': {'direction_pin': 13, 'step_pin': 11},
            'y': {'direction_pin': 38, 'step_pin': 40},
            'z': {'direction_pin': 8, 'step_pin': 10}}

    direction_pin = axis[a]['direction_pin']
    step_pin = axis[a]['step_pin']

    steps = 10000
    velocity = 1000

    # Set board's GPIO pins
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(direction_pin, GPIO.OUT)
    GPIO.setup(step_pin, GPIO.OUT)

    GPIO.output(direction_pin, CCW)
    for _ in tqdm(range(steps)):
        motor_single_step(step_pin, velocity)

    # time.sleep(2)
    #
    # GPIO.output(direction_pin, CCW)
    # for _ in tqdm(range(steps)):
    #     motor_single_step(step_pin, velocity)

    GPIO.cleanup()
