import RPi.GPIO as GPIO
import time
import multiprocessing
from multiprocessing.managers import BaseManager
from gpiozero import Button


class Motor:
    def __init__(self, motor_name, direction_pin, step_pin, kill_switch_i_pin, kill_switch_f_pin,
                 direction, step_resolution):
        self.motor_name = motor_name
        self.direction_pin = direction_pin
        self.step_pin = step_pin
        self.kill_switch_i_pin = kill_switch_i_pin
        self.kill_switch_f_pin = kill_switch_f_pin
        self.step_counter = 0
        self.direction = direction
        self.velocity = 0
        self.current_position = 0
        self.motor_setup()
        self.kill_switch_i_state = GPIO.input(self.kill_switch_i_pin)
        self.kill_switch_f_state = GPIO.input(self.kill_switch_f_pin)
        self.step_resolution = step_resolution
        self.stop = 0
        self.done_running = False

    def motor_setup(self):
        # This function sets up the motor's pins for initial use
        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.kill_switch_i_pin, GPIO.IN)
        GPIO.setup(self.kill_switch_f_pin, GPIO.IN)

    def check_motor_kill_switches(self):
        # This function reads the off switch status and updates it's state in the object
        self.kill_switch_i_state = GPIO.input(self.kill_switch_i_pin)
        self.kill_switch_f_state = GPIO.input(self.kill_switch_f_pin)
        # print(self.kill_switch_i_state, self.kill_switch_f_state)
        if self.kill_switch_i_state or self.kill_switch_f_state:
            # self.stop = 1
            pass

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
            self.current_position += self.step_resolution
        else:
            self.current_position -= self.step_resolution

    def motor_while_loop(self, velocity, direction):
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(self.direction_pin, direction)
        while not self.stop and velocity != 0:
            self.motor_single_step(velocity)
            self.update_motor_status(velocity, direction)
            self.check_motor_kill_switches()
        self.done_running = True

    def motor_for_loop(self, velocity, direction, step_amount):
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(self.direction_pin, direction)
        for _step in range(step_amount):
            if not self.stop and velocity != 0:
                self.motor_single_step(velocity)
                self.update_motor_status(velocity, direction)
                self.check_motor_kill_switches()
        self.done_running = True

    def get_values(self):
        # This function returns all the motor's attributes
        return {'motor_name': self.motor_name,
                'direction_pin': self.direction_pin,
                'step_pin': self.step_pin,
                'off_switch_pin': self.off_switch_pin,
                'step_counter': self.step_counter,
                'direction': self.direction,
                'velocity': self.velocity,
                'current_position': self.current_position,
                'off_switch': self.kill_switch_i_state,
                'done_running': self.done_running}

    def get_dynamic_values(self):
        # This function returns all the motor's dynamic attributes
        return {'step_counter': self.step_counter,
                'direction': self.direction,
                'velocity': self.velocity,
                'current_position': self.current_position,
                'off_switch': self.kill_switch_i_state,
                'done_running': self.done_running}

    def reset_motor_run(self):
        self.done_running = False


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
                              kill_switch_i_pin=22, kill_switch_f_pin=24, direction=CW, step_resolution=0.05)
    motor_two = manager.Motor(motor_name='motor 2', direction_pin=38, step_pin=40,
                              kill_switch_i_pin=22, kill_switch_f_pin=24, direction=CW, step_resolution=0.05)

    # These are the motors movement instructions
    instructions = [{'velocity_1': 200, 'direction_1': CW, 'step_amount_1': 500,
                     'velocity_2': 200, 'direction_2': CW, 'step_amount_2': 1000},
                    {'velocity_1': 200, 'direction_1': CCW, 'step_amount_1': 250,
                     'velocity_2': 100, 'direction_2': CCW, 'step_amount_2': 50}]

    # This is the programs main loop, going through the instructions provided
    for step, instruction in enumerate(instructions):
        velocity_1 = instruction['velocity_1']
        direction_1 = instruction['direction_1']
        velocity_2 = instruction['velocity_2']
        direction_2 = instruction['direction_2']
        step_amount_1 = instruction['step_amount_1']
        step_amount_2 = instruction['step_amount_2']

        print(f'Step #{step + 1}: \n'
              f'motor #1 will move in speed {instruction["velocity_1"]} [steps/second] in direction '
              f'{instruction["direction_1"]}\n'
              f'motor #2 will move in speed {instruction["velocity_2"]} [steps/second] in direction '
              f'{instruction["direction_2"]}')

        # Set a movement process for each motor
        motor_one_process = multiprocessing.Process(target=motor_one.motor_for_loop,
                                                    args=(velocity_1, direction_1, step_amount_1, ))
        motor_two_process = multiprocessing.Process(target=motor_two.motor_for_loop,
                                                    args=(velocity_2, direction_2, step_amount_2, ))

        # Start the process
        motor_one_process.start()
        motor_two_process.start()

        # Wait for process to run
        # time.sleep(instruction['step_duration'])
        not_done = True
        while not_done:
            # Get updated dynamic values
            motor_one_status = motor_one.get_dynamic_values()
            motor_two_status = motor_two.get_dynamic_values()

            # check if all motors are done
            if motor_one_status['done_running'] and motor_two_status['done_running']:
                not_done = False

        print(f'Current Motor 1 status - {motor_one_status}')
        print(f'Current Motor 2 status - {motor_two_status}\n\n')

        # Kill movement process
        motor_one_process.kill()
        motor_two_process.kill()

        # reset the motor's run flag
        motor_one.reset_motor_run()
        motor_two.reset_motor_run()

    GPIO.cleanup()
