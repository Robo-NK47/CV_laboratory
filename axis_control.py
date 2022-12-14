import RPi.GPIO as GPIO
import time
from gpiozero import Button as KillSwitch


class Axis:
    def __init__(self, axis_name, direction_pin, step_pin, kill_switch_i_pin, kill_switch_f_pin,
                 direction, step_resolution, axis_length):
        self.directions = {'up': 1, 'down': 0, 'left': 1, 'right': 0, 'forward': 1, 'backward': 0}
        self.velocity = 0
        self.current_position = 0
        self.step_counter = 0
        self.stop = 0  # a condition triggered by one of the kill switches

        self.axis_name = axis_name
        self.direction_pin = direction_pin
        self.step_pin = step_pin
        self.step_resolution = step_resolution
        self.direction = self.directions[direction]
        self.axis_length = axis_length

        self.kill_switch_i_pin = kill_switch_i_pin  # switch at 0
        self.kill_switch_f_pin = kill_switch_f_pin  # switch at axis_length
        self.kill_switch_i = KillSwitch(kill_switch_i_pin)  # switch at 0
        self.kill_switch_f = KillSwitch(kill_switch_f_pin)  # switch at axis_length
        self.kill_switch_i_state = self.kill_switch_i.is_pressed  # switch at 0
        self.kill_switch_f_state = self.kill_switch_f.is_pressed  # switch at axis_length

        self.check_axis_kill_switches()
        self.axis_setup()

    def axis_setup(self):
        # This function sets up the motor's pins for initial use
        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)

    def check_axis_kill_switches(self):
        # This function reads the off switch status and updates it's state in the object
        self.kill_switch_i_state = self.kill_switch_i.is_pressed
        self.kill_switch_f_state = self.kill_switch_f.is_pressed

        if (self.kill_switch_i_state and not self.direction) or (self.kill_switch_f_state and self.direction):
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

        self.current_position = round(self.current_position, 3)

    def axis_while_loop(self, velocity, direction, next_position):
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(self.direction_pin, direction)
        while not self.stop and velocity != 0 and self.current_position != next_position:
            self.motor_single_step(velocity)
            self.update_axis_status(velocity, direction)
            self.check_axis_kill_switches()

    def axis_for_loop(self, velocity, direction, step_amount):
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(self.direction_pin, direction)
        for _step in range(step_amount):
            if not self.stop and velocity != 0:
                self.motor_single_step(velocity)
                self.update_axis_status(velocity, direction)
                self.check_axis_kill_switches()
            else:
                break

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

    def go_to_home_position(self, home_position):
        direction = self.direction
        velocity = 1000
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(self.direction_pin, direction)

        print(f'{self.axis_name}: going to position 0.')
        while not self.stop:
            self.motor_single_step(velocity)
            self.update_axis_status(velocity, direction)
            self.check_axis_kill_switches()

        self.current_position = 0
        print(f'{self.axis_name}: going to home position.')
        direction = not self.direction
        GPIO.output(self.direction_pin, direction)
        for _ in range(int(home_position / self.step_resolution)):
            self.motor_single_step(velocity)
            self.update_axis_status(velocity, direction)
            self.check_axis_kill_switches()
