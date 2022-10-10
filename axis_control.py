import RPi.GPIO as GPIO
import time
import multiprocessing
from multiprocessing.managers import BaseManager
from gpiozero import Button
from tqdm.auto import tqdm
from tkinter import *
from tkinter.ttk import Style


class Axis:
    def __init__(self, axis_name, direction_pin, step_pin, kill_switch_i_pin, kill_switch_f_pin,
                 direction, step_resolution, axis_length):
        self.axis_name = axis_name
        self.direction_pin = direction_pin
        self.step_pin = step_pin
        self.kill_switch_i_pin = kill_switch_i_pin
        self.kill_switch_f_pin = kill_switch_f_pin
        self.kill_switch_i = Button(kill_switch_i_pin)
        self.kill_switch_f = Button(kill_switch_f_pin)
        self.step_counter = 0
        self.direction = direction
        self.velocity = 0
        self.current_position = 0
        self.axis_setup()
        self.kill_switch_i_state = self.kill_switch_i.is_pressed
        self.kill_switch_f_state = self.kill_switch_f.is_pressed
        self.step_resolution = step_resolution
        self.stop = 0
        self.done_running = False
        self.axis_length = axis_length

    def axis_setup(self):
        # This function sets up the motor's pins for initial use
        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)

    def check_axis_kill_switches(self):
        # This function reads the off switch status and updates it's state in the object
        self.kill_switch_i_state = self.kill_switch_i.is_pressed
        self.kill_switch_f_state = self.kill_switch_f.is_pressed
        # print(self.kill_switch_i_state, self.kill_switch_f_state)
        if self.kill_switch_i_state or self.kill_switch_f_state:
            self.stop = 1

        else:
            self.stop = 0

    def motor_single_step(self, velocity):
        # This function makes the motor moves a single step in a defined time interval
        GPIO.output(self.step_pin, GPIO.HIGH)
        time.sleep(0.5 * (1 / velocity))
        GPIO.output(self.step_pin, GPIO.LOW)
        time.sleep(0.5 * (1 / velocity))

    def update_axis_status(self, velocity, direction):
        # This function updates the motor's dynamic values
        self.step_counter += 1
        self.velocity = velocity
        self.direction = direction

        if self.direction == 1:
            self.current_position += self.step_resolution
        else:
            self.current_position -= self.step_resolution

    def axis_while_loop(self, velocity, direction, next_position):
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(self.direction_pin, direction)
        while not self.stop and velocity != 0 and round(self.current_position,3) != round(next_position, 3):
            self.motor_single_step(velocity)
            self.update_axis_status(velocity, direction)
            self.check_axis_kill_switches()
        self.done_running = True

    def axis_for_loop(self, velocity, direction, step_amount):
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(self.direction_pin, direction)
        for _step in range(step_amount):
            if not self.stop and velocity != 0:
                self.motor_single_step(velocity)
                self.update_axis_status(velocity, direction)
                self.check_axis_kill_switches()
            else:
                self.done_running = True
                break
        self.done_running = True

    def get_values(self):
        # This function returns all the motor's attributes
        return {'axis_name': self.axis_name,
                'axis_length': self.axis_length,
                'step_resolution': self.step_resolution,
                'direction_pin': self.direction_pin,
                'step_pin': self.step_pin,
                'kill_switch_i_pin': self.kill_switch_i_pin,
                'kill_switch_f_pin': self.kill_switch_f_pin,
                'step_counter': self.step_counter,
                'direction': self.direction,
                'velocity': self.velocity,
                'current_position': self.current_position,
                'i_off_switch': self.kill_switch_i_state,
                'f_off_switch': self.kill_switch_f_state,
                'done_running': self.done_running}

    def reset_axis_run(self):
        self.done_running = False

    def go_to_home_position(self, home_position):
        direction = 0
        velocity = 200
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(self.direction_pin, direction)
        print(f'Axis {self.axis_name}: going to position 0.')
        while not self.stop:
            self.motor_single_step(velocity)
            self.update_axis_status(velocity, direction)
            self.check_axis_kill_switches()
        self.current_position = 0
        print(f'Axis {self.axis_name}: going to home position.')
        direction = 1
        GPIO.output(self.direction_pin, direction)
        for _ in tqdm(range(int(home_position / self.step_resolution))):
            self.motor_single_step(velocity)
            self.update_axis_status(velocity, direction)
            self.check_axis_kill_switches()
        self.done_running = True


def calc_instructions_for_next_position(axis_status, next_position):
    current_position = axis_status['current_position']
    axis_resolution = axis_status['step_resolution']
    delta = abs(current_position - next_position)
    steps = int(delta / axis_resolution)

    if next_position > current_position:
        next_direction = 1

    if next_position < current_position:
        next_direction = 0

    if next_position == current_position:
        next_direction = 1
        steps = 0

    return {'steps_amount': steps, 'direction': next_direction}


def homing_sequence(_x_axis, _y_axis, _x_axis_home_position, _y_axis_home_position):
    _x_axis_process = multiprocessing.Process(target=_x_axis.go_to_home_position, args=(_x_axis_home_position,))
    _y_axis_process = multiprocessing.Process(target=_y_axis.go_to_home_position, args=(_y_axis_home_position,))

    _x_axis_process.start()
    _y_axis_process.start()

    _not_done = True
    while _not_done:
        # Get updated dynamic values
        _x_axis_status = _x_axis.get_values()
        _y_axis_status = _y_axis.get_values()

        # check if all motors are done
        if _x_axis_status['done_running'] and _y_axis_status['done_running']:
            _not_done = False

    print(f"Current {_x_axis_status['axis_name']} position - {_x_axis_status['current_position']:.2f} [mm]")
    print(f"Current {_y_axis_status['axis_name']} position - {_y_axis_status['current_position']:.2f} [mm]\n")

    # Kill movement process
    _x_axis_process.kill()
    _y_axis_process.kill()
    _x_axis.reset_axis_run()
    _y_axis.reset_axis_run()


if __name__ == "__main__":

    x_axis_home_position = 100
    y_axis_home_position = 50

    # 0/1 used to define clockwise or counterclockwise.
    CW = 1
    CCW = 0

    # Set board's GPIO pins
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    # Create axis objects in a multiprocessing manner
    BaseManager.register('Axis', Axis)
    manager = BaseManager()
    manager.start()
    x_axis = manager.Axis(axis_name='X axis', direction_pin=10, step_pin=8, kill_switch_i_pin=23,
                          kill_switch_f_pin=26, direction=CW, step_resolution=0.05, axis_length=1000)
    y_axis = manager.Axis(axis_name='Y axis', direction_pin=38, step_pin=40, kill_switch_i_pin=24,
                          kill_switch_f_pin=27, direction=CW, step_resolution=0.05, axis_length=1500)

    homing_sequence(x_axis, y_axis, x_axis_home_position, y_axis_home_position)

    x_axis_status = x_axis.get_values()
    y_axis_status = y_axis.get_values()

    # These are the axis movement instructions
    instructions = [{'velocity': {'x': 300, 'y': 500}, 'position': {'x': 500, 'y': 0}},
                    {'velocity': {'x': 400, 'y': 400}, 'position': {'x': 500, 'y': 500}},
                    {'velocity': {'x': 500, 'y': 300}, 'position': {'x': 0, 'y': 0}}]

    _ = input('Press enter twice to begin sequence.')
    # This is the programs main loop, going through the instructions provided
    for step, instruction in enumerate(instructions):

        x_instructions = calc_instructions_for_next_position(x_axis_status, instruction['position']['x'])
        x_axis_velocity = instruction['velocity']['x']
        x_axis_direction = x_instructions['direction']

        y_instructions = calc_instructions_for_next_position(y_axis_status, instruction['position']['y'])
        y_axis_velocity = instruction['velocity']['y']
        y_axis_direction = y_instructions['direction']

        print(f'Step #{step + 1}: \n'
              f"From ({x_axis_status['current_position']:.2f}, {y_axis_status['current_position']:.2f}) [mm] to "
              f"({instruction['position']['x']:.2f}, {instruction['position']['y']:.2f}) [mm] in speeds of "
              f"({instruction['velocity']['x']}, {instruction['velocity']['y']}) [steps/second].")

        # Set a movement process for each axis
        x_axis_process = multiprocessing.Process(target=x_axis.axis_while_loop,
                                                 args=(x_axis_velocity, x_axis_direction,
                                                       instruction['position']['x'],))
        y_axis_process = multiprocessing.Process(target=y_axis.axis_while_loop,
                                                 args=(y_axis_velocity, y_axis_direction,
                                                       instruction['position']['y'],))

        # Start the process
        x_axis_process.start()
        y_axis_process.start()

        # Wait for process to run
        not_done = True
        while not_done:
            # Get updated values
            x_axis_status = x_axis.get_values()
            y_axis_status = y_axis.get_values()

            # check if all axis are done
            if x_axis_status['done_running'] and y_axis_status['done_running']:
                not_done = False

        print(f"Current {x_axis_status['axis_name']} position - {abs(x_axis_status['current_position']):.2f} [mm]")
        print(f"Current {y_axis_status['axis_name']} position - {abs(y_axis_status['current_position']):.2f} [mm]\n")

        # Kill movement process
        x_axis_process.kill()
        y_axis_process.kill()

        # reset the axis's run flag
        x_axis.reset_axis_run()
        y_axis.reset_axis_run()

    GPIO.cleanup()
