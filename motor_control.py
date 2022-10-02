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
        self.current_angle = 0
        self.motor_setup()
        self.off_switch = GPIO.input(self.off_switch_pin)
        self.step_amount = step_amount
        self.angle_check = []

    def motor_setup(self):
        # This function sets up the motor's pins for initial use
        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.off_switch_pin, GPIO.IN)

    def check_motor_switch(self):
        # This function reads the off switch status and updates it's state in the object
        self.off_switch = GPIO.input(self.off_switch_pin)

    def motor_single_step(self, velocity):
        # This function makes the motor moves a single step in a defined time interval
        GPIO.output(self.step_pin, GPIO.HIGH)
        time.sleep(0.5 * (1/velocity))
        GPIO.output(self.step_pin, GPIO.LOW)
        time.sleep(0.5 * (1/velocity))

    def update_motor_status(self, velocity, direction):
        # This function updates the motor's dynamic values
        self.step_counter += 1
        self.velocity = velocity
        self.direction = direction

        if self.direction == 1:
            self.current_angle += (360 / self.step_amount)
        else:
            self.current_angle -= (360 / self.step_amount)
        self.monitor_current_position()
        self.angle_check.append(self.current_angle)

    def monitor_current_position(self):
        # Updates the motor's current angle, from 0 to 360 in degrees
        if int(self.current_angle) == 360:
            self.current_angle = 0

        if self.current_angle < 0:
            self.current_angle = ((360 / self.step_amount) * (self.step_amount - 1)) + self.current_angle

    def motor_loop(self, velocity, direction):
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(self.direction_pin, direction)
        while self.off_switch and velocity != 0:
            self.motor_single_step(velocity)
            self.update_motor_status(velocity, direction)
            self.check_motor_switch()

    def get_values(self):
        # This function returns all the motor's attributes
        return {'motor_name': self.motor_name,
                'direction_pin': self.direction_pin,
                'step_pin': self.step_pin,
                'off_switch_pin': self.off_switch_pin,
                'step_counter': self.step_counter,
                'direction': self.direction,
                'velocity': self.velocity,
                'current_position': self.current_angle,
                'off_switch': self.off_switch}

    def get_dynamic_values(self):
        # This function returns all the motor's dynamic attributes
        return {'step_counter': self.step_counter,
                'direction': self.direction,
                'velocity': self.velocity,
                'current_position': self.current_angle,
                'off_switch': self.off_switch}


if __name__ == "__main__":
    # 0/1 used to define clockwise or counterclockwise.
    CW = 1
    CCW = 0

    # Set board's GPIO pins
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    # Create motor objects in a multiprocessing manner
    BaseManager.register('Motor', Motor)
    manager = BaseManager()
    manager.start()
    motor_one = manager.Motor(motor_name='motor 1', direction_pin=10, step_pin=8,
                              off_switch_pin=22, direction=CW, step_amount=200)
    motor_two = manager.Motor(motor_name='motor 2', direction_pin=38, step_pin=40,
                              off_switch_pin=22, direction=CW, step_amount=200)

    # These are the motors movement instructions
    instructions = [{'velocity_1': 100, 'direction_1': CW,
                     'velocity_2': 100, 'direction_2': CW, 'step_duration': 2},
                    {'velocity_1': 200, 'direction_1': CCW,
                     'velocity_2': 0, 'direction_2': CW, 'step_duration': 2},
                    {'velocity_1': 0, 'direction_1': CCW,
                     'velocity_2': 200, 'direction_2': CCW, 'step_duration': 2},
                    {'velocity_1': 100, 'direction_1': CW,
                     'velocity_2': 200, 'direction_2': CCW, 'step_duration': 2},
                    {'velocity_1': 150, 'direction_1': CCW,
                     'velocity_2': 150, 'direction_2': CCW, 'step_duration': 2}]

    # This is the programs main loop, going through the instructions provided
    for step, instruction in enumerate(instructions):
        velocity_1 = instruction['velocity_1']
        direction_1 = instruction['direction_1']
        velocity_2 = instruction['velocity_2']
        direction_2 = instruction['direction_2']

        print(f'Step #{step + 1}, for an interval of {instruction["step_duration"]} seconds: \n'
              f'motor #1 will move in speed {instruction["velocity_1"]} [steps/second] in direction '
              f'{instruction["direction_1"]}\n' 
              f'motor #2 will move in speed {instruction["velocity_2"]} [steps/second] in direction '
              f'{instruction["direction_2"]}')

        # Set a movement process for each motor
        motor_one_process = multiprocessing.Process(target=motor_one.motor_loop, args=(velocity_1, direction_1, ))
        motor_two_process = multiprocessing.Process(target=motor_two.motor_loop, args=(velocity_2, direction_2, ))

        # Start the process
        motor_one_process.start()
        motor_two_process.start()

        # Wait for process to run
        time.sleep(instruction['step_duration'])

        # Get updated dynamic values
        motor_one_status = motor_one.get_dynamic_values()
        motor_two_status = motor_two.get_dynamic_values()

        print(f'Current Motor 1 status - {motor_one_status}')
        print(f'Current Motor 2 status - {motor_two_status}\n\n')

        # Kill movement process
        motor_one_process.kill()
        motor_two_process.kill()

    GPIO.cleanup()

    print('a')