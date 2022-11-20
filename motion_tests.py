import RPi.GPIO as GPIO
import time
import multiprocessing
from multiprocessing.managers import BaseManager
from gpiozero import Button
from tqdm.auto import tqdm


class Axis:
    def __init__(self, axis_name, direction_pin, step_pin, kill_switch_i_pin, kill_switch_f_pin,
                 direction, step_resolution, axis_length):
        self.directions = {'up': 1, 'down': 0, 'left': 1, 'right': 0, 'forward': 1, 'backward': 0}
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
        self.stop = 0  # a condition triggered by one of the kill switches
        self.done_running = False  # a boolean flag for the main process, True when the movement is done
        self.axis_length = axis_length
        self.check_axis_kill_switches()

    def axis_setup(self):
        # This function sets up the motor's pins for initial use
        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)

    def check_axis_kill_switches(self):
        # This function reads the off switch status and updates it's state in the object
        self.kill_switch_i_state = self.kill_switch_i.is_pressed
        self.kill_switch_f_state = self.kill_switch_f.is_pressed
        # print(self.kill_switch_i_state, self.kill_switch_f_state)
        if self.kill_switch_i_state:
            self.stop = 1
            self.done_running = True
            self.current_position = 0

        elif self.kill_switch_f_state:
            self.stop = 1
            self.done_running = True
            self.current_position = self.axis_length

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

        self.current_position = round(self.current_position, 3)

        if self.current_position < 0:
            self.stop = 1
            self.done_running = True
            self.current_position = 0

        if self.current_position > self.axis_length:
            self.stop = 1
            self.done_running = True
            self.current_position = self.axis_length

    def axis_while_loop(self, velocity, _direction, next_position):
        self.direction = _direction
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(self.direction_pin, self.direction)
        while not self.stop and velocity != 0 and self.current_position != next_position:
            self.motor_single_step(velocity)
            self.update_axis_status(velocity, self.direction)
            # self.check_axis_kill_switches()
            print(self.direction, self.step_counter, self.current_position)
        self.done_running = True
        print(" ")

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

    def reset_axis_run(self):
        self.done_running = False

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


if __name__ == "__main__":
    x_axis_home_position = 100
    y_axis_home_position = 50
    z_axis_home_position = 100

    # 0/1 used to define clockwise or counterclockwise.
    CW = 1
    CCW = 0
    directions = {'up': CW, 'down': CCW, 'left': CW, 'right': CCW, 'forward': CW, 'backward': CCW}

    # Set board's GPIO pins
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    # Create axis objects in a multiprocessing manner
    x_axis = Axis(axis_name='X axis', direction_pin=31, step_pin=29, kill_switch_i_pin=10,
                  kill_switch_f_pin=11, direction=CW, step_resolution=0.05, axis_length=1500)

    y_axis = Axis(axis_name='Y axis', direction_pin=38, step_pin=40, kill_switch_i_pin=24,
                  kill_switch_f_pin=27, direction=CW, step_resolution=0.05, axis_length=500)

    z_axis = Axis(axis_name='Z axis', direction_pin=8, step_pin=10, kill_switch_i_pin=23,
                  kill_switch_f_pin=26, direction=CW, step_resolution=0.05, axis_length=2000)

    x_axis.axis_for_loop(500, 1, 1000)
    x_axis.axis_for_loop(500, 0, 1000)

    y_axis.axis_for_loop(500, 1, 1000)
    y_axis.axis_for_loop(500, 0, 1000)

    z_axis.axis_for_loop(500, 1, 1000)
    z_axis.axis_for_loop(500, 0, 1000)

    GPIO.cleanup()
