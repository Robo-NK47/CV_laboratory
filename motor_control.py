import RPi.GPIO as GPIO
import time
import multiprocessing


class Motor:
    def __init__(self, motor_name, direction_pin, step_pin, motor_off_switch_pin, direction):
        self.motor_name = motor_name
        self.direction_pin = direction_pin
        self.step_pin = step_pin
        self.motor_off_switch_pin = motor_off_switch_pin
        self.step_counter = 0
        self.direction = direction
        self.velocity = 0
        self.current_position = 0
        self.motor_setup()
        self.motor_switch_off = GPIO.input(self.motor_off_switch_pin)

    def motor_setup(self):
        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.motor_off_switch_pin, GPIO.IN)

    def check_motor_switch(self):
        self.motor_switch_off = GPIO.input(self.motor_off_switch_pin)

    def motor_single_step(self, velocity):
        GPIO.output(self.step_pin, GPIO.HIGH)
        time.sleep(0.5 * velocity)
        GPIO.output(self.step_pin, GPIO.LOW)
        time.sleep(0.5 * velocity)

    def update_motor_status(self):
        self.step_counter += 1

        if self.direction == 1:
            self.current_position += 1
        else:
            self.current_position -= 1

    def motor_loop(self, velocity, direction):
        GPIO.output(self.direction_pin, direction)
        while self.motor_switch_off and velocity != 0:  # and self.step_counter <= 200:
            self.motor_single_step(velocity)
            self.update_motor_status()
            self.check_motor_switch()


if __name__ == "__main__":
    # 0/1 used to define clockwise or counterclockwise.
    CW = 1
    CCW = 0

    # Set board's GPIO pins
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    motor_steps_dictionary = {}

    # set GPIO pins
    motor_one_direction_pin = 10
    motor_one_step_pin = 8
    motor_one_off_switch_pin = 22

    motor_two_direction_pin = 38
    motor_two_step_pin = 40
    motor_two_off_switch_pin = 22

    # Create motor objects
    motor_one = Motor('motor 1', motor_one_direction_pin, motor_one_step_pin, motor_one_off_switch_pin, 1)
    motor_two = Motor('motor 2', motor_two_direction_pin, motor_two_step_pin, motor_two_off_switch_pin, 1)

    instructions = [{'velocity_1': 0.01, 'direction_1': 1, 'velocity_2': 0.02, 'direction_2': 1, 'step_duration': 2},
                    {'velocity_1': 0.02, 'direction_1': 0, 'velocity_2': 0, 'direction_2': 1, 'step_duration': 3},
                    {'velocity_1': 0, 'direction_1': 0, 'velocity_2': 0.002, 'direction_2': 0, 'step_duration': 3},
                    {'velocity_1': 0.001, 'direction_1': 1, 'velocity_2': 0.002, 'direction_2': 0, 'step_duration': 3},
                    {'velocity_1': 0.01, 'direction_1': 0, 'velocity_2': 0.01, 'direction_2': 0, 'step_duration': 2}]

    for step, instruction in enumerate(instructions):
        velocity_1 = instruction['velocity_1']
        direction_1 = instruction['direction_1']
        velocity_2 = instruction['velocity_2']
        direction_2 = instruction['direction_2']

        print(f'Step #{step + 1}, for an interval of {instruction["step_duration"]} seconds: \n'
              f'motor #1 will move in speed {instruction["velocity_1"]} in direction {instruction["direction_1"]}\n'
              f'motor #2 will move in speed {instruction["velocity_2"]} in direction {instruction["direction_2"]}\n\n')

        motor_one_process = multiprocessing.Process(target=motor_one.motor_loop, args=(velocity_1, direction_1, ))
        motor_two_process = multiprocessing.Process(target=motor_two.motor_loop, args=(velocity_2, direction_2, ))

        motor_one_process.start()
        motor_two_process.start()

        time.sleep(instruction['step_duration'])

        motor_one_process.kill()
        motor_two_process.kill()

    GPIO.cleanup()
