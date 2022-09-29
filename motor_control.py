import RPi.GPIO as GPIO
import time
import multiprocessing
from multiprocessing.managers import BaseManager


class Motor:
    def __init__(self, motor_name, direction_pin, step_pin, off_switch_pin, direction, step_amount):
        self.motor_name = motor_name
        self.direction_pin = direction_pin
        self.step_pin = step_pin
        self.off_switch_pin = off_switch_pin
        self.step_counter = 0
        self.direction = direction
        self.velocity = 0
        self.current_position = 0
        self.motor_setup()
        self.off_switch = GPIO.input(self.off_switch_pin)
        self.step_amount = step_amount

    def motor_setup(self):
        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.off_switch_pin, GPIO.IN)

    def check_motor_switch(self):
        self.off_switch = GPIO.input(self.off_switch_pin)

    def motor_single_step(self, velocity):
        GPIO.output(self.step_pin, GPIO.HIGH)
        time.sleep(0.5 * velocity)
        GPIO.output(self.step_pin, GPIO.LOW)
        time.sleep(0.5 * velocity)

    def update_motor_status(self, velocity, direction):
        self.step_counter += 1
        self.velocity = velocity
        self.direction = direction

        if self.direction == 1:
            self.current_position += 1
        else:
            self.current_position -= 1
        self.monitor_current_position()

    def monitor_current_position(self):
        if self.current_position == self.step_amount:
            self.current_position = 0

        if self.current_position < 0:
            self.current_position = (self.step_amount - 1) + self.current_position

    def motor_loop(self, velocity, direction):

        GPIO.output(self.direction_pin, direction)
        while self.off_switch and velocity != 0:  # and self.step_counter < 200:
            self.motor_single_step(velocity)
            self.update_motor_status(velocity, direction)
            self.check_motor_switch()

    def get_values(self):
        return {'motor_name': self.motor_name,
                'direction_pin': self.direction_pin,
                'step_pin': self.step_pin,
                'off_switch_pin': self.off_switch_pin,
                'step_counter': self.step_counter,
                'direction': self.direction,
                'velocity': self.velocity,
                'current_position': self.current_position,
                'off_switch': self.off_switch}

    def get_dynamic_values(self):
        return {'step_counter': self.step_counter,
                'direction': self.direction,
                'velocity': self.velocity,
                'current_position': self.current_position,
                'off_switch': self.off_switch}


if __name__ == "__main__":
    # 0/1 used to define clockwise or counterclockwise.
    CW = 1
    CCW = 0

    # Set board's GPIO pins
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    # Create motor objects
    BaseManager.register('Motor', Motor)
    manager = BaseManager()
    manager.start()
    motor_one = manager.Motor(motor_name='motor 1', direction_pin=10, step_pin=8,
                              off_switch_pin=22, direction=CW, step_amount=200)
    motor_two = manager.Motor(motor_name='motor 2', direction_pin=38, step_pin=40,
                              off_switch_pin=22, direction=CW, step_amount=200)

    instructions = [{'velocity_1': 0.01, 'direction_1': CW,
                     'velocity_2': 0.02, 'direction_2': CW, 'step_duration': 10}]
        # ,
        #             {'velocity_1': 0.02, 'direction_1': CCW,
        #              'velocity_2': 0, 'direction_2': CW, 'step_duration': 10},
        #             {'velocity_1': 0, 'direction_1': CCW,
        #              'velocity_2': 0.002, 'direction_2': CCW, 'step_duration': 10},
        #             {'velocity_1': 0.001, 'direction_1': CW,
        #              'velocity_2': 0.002, 'direction_2': CCW, 'step_duration': 10},
        #             {'velocity_1': 0.01, 'direction_1': CCW,
        #              'velocity_2': 0.01, 'direction_2': CCW, 'step_duration': 10}]

    for step, instruction in enumerate(instructions):
        velocity_1 = instruction['velocity_1']
        direction_1 = instruction['direction_1']
        velocity_2 = instruction['velocity_2']
        direction_2 = instruction['direction_2']

        print(f'Step #{step + 1}, for an interval of {instruction["step_duration"]} seconds: \n'
              f'motor #1 will move in speed {instruction["velocity_1"]} in direction {instruction["direction_1"]}\n'
              f'motor #2 will move in speed {instruction["velocity_2"]} in direction {instruction["direction_2"]}')

        motor_one_process = multiprocessing.Process(target=motor_one.motor_loop, args=(velocity_1, direction_1, ))
        motor_two_process = multiprocessing.Process(target=motor_two.motor_loop, args=(velocity_2, direction_2, ))

        motor_one_process.start()
        motor_two_process.start()

        time.sleep(instruction['step_duration'])

        print(f'Current Motor 1 status - {motor_one.get_dynamic_values()}')
        print(f'Current Motor 2 status - {motor_two.get_dynamic_values()}\n\n')

        motor_one_process.kill()
        motor_two_process.kill()

    GPIO.cleanup()
