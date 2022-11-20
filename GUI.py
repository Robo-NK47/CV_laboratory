from tkinter import *
from PIL import ImageTk, Image
from tkinter import ttk
from tqdm.auto import tqdm
import threading
from gpiozero import Button as KillSwitch
import RPi.GPIO as GPIO
import time


class Axis:
    def __init__(self, axis_name, direction_pin, step_pin, kill_switch_i_pin, kill_switch_f_pin,
                 direction, step_resolution, axis_length):
        self.directions = {'up': 1, 'down': 0, 'left': 0, 'right': 1, 'forward': 1, 'backward': 0}
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
                'f_off_switch': self.kill_switch_f_state}

    def go_to_home_position(self, home_position):
        direction = self.direction
        velocity = 1000
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(self.direction_pin, direction)

        print(f'{self.axis_name}: going to position 0.')
        while not self.stop:
            self.check_axis_kill_switches()
            self.motor_single_step(velocity)
            self.update_axis_status(velocity, direction)

        self.current_position = 0
        print(f'{self.axis_name}: going to home position.')
        direction = not self.direction
        GPIO.output(self.direction_pin, direction)
        for _ in range(int(home_position / self.step_resolution)):
            self.check_axis_kill_switches()
            self.motor_single_step(velocity)
            self.update_axis_status(velocity, direction)


def update_current_position():
    global x_axis
    global y_axis
    global z_axis
    global current_position_entry

    current_position = (x_axis.current_position, y_axis.current_position, z_axis.current_position)
    current_position_entry.delete(0, 'end')
    current_position_entry.insert(END, str(current_position))


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


def homing_sequence():
    global x_axis
    global y_axis
    global z_axis

    x_homing_thread = threading.Thread(target=x_axis.go_to_home_position, args=(int(x_axis.axis_length * 0.5),))
    y_homing_thread = threading.Thread(target=y_axis.go_to_home_position, args=(int(y_axis.axis_length * 0.5),))
    z_homing_thread = threading.Thread(target=z_axis.go_to_home_position, args=(int(z_axis.axis_length * 0.5),))
    x_homing_thread.start()
    y_homing_thread.start()
    z_homing_thread.start()
    x_homing_thread.join()
    y_homing_thread.join()
    z_homing_thread.join()

    update_current_position()


def which_axis(axis_name):
    if axis_name == 'x':
        return x_axis
    if axis_name == 'y':
        return y_axis
    if axis_name == 'z':
        return z_axis


def create_motion(axis_name, direction, steps, velocity):
    if steps > 0:
        axis = which_axis(axis_name)
        axis.stop = False

        direction = axis.directions[direction]
        # Main motor function, moves the motor and updates it's dynamic values
        GPIO.output(axis.direction_pin, direction)
        axis.check_axis_kill_switches()
        for _ in tqdm(range(steps)):
            if not axis.stop:
                axis.check_axis_kill_switches()
                axis.motor_single_step(velocity)
                axis.update_axis_status(velocity, direction)
    return None
    # print(f'Current position: ({x_axis.current_position}, {y_axis.current_position}, {z_axis.current_position}) [mm]')


def free_move_up():
    global free_motion_velocity_entry
    global free_motion_steps_entry

    free_motion_velocity = float(free_motion_velocity_entry.get())
    free_motion_steps = int(free_motion_steps_entry.get())
    create_motion('y', 'up', free_motion_steps, free_motion_velocity)
    update_current_position()


def free_move_down():
    global free_motion_velocity_entry
    global free_motion_steps_entry

    free_motion_velocity = float(free_motion_velocity_entry.get())
    free_motion_steps = int(free_motion_steps_entry.get())
    create_motion('y', 'down', free_motion_steps, free_motion_velocity)
    update_current_position()


def free_move_left():
    global free_motion_velocity_entry
    global free_motion_steps_entry

    free_motion_velocity = float(free_motion_velocity_entry.get())
    free_motion_steps = int(free_motion_steps_entry.get())
    create_motion('x', 'left', free_motion_steps, free_motion_velocity)
    update_current_position()


def free_move_right():
    global free_motion_velocity_entry
    global free_motion_steps_entry

    free_motion_velocity = float(free_motion_velocity_entry.get())
    free_motion_steps = int(free_motion_steps_entry.get())
    create_motion('x', 'right', free_motion_steps, free_motion_velocity)
    update_current_position()


def free_move_forward():
    global free_motion_velocity_entry
    global free_motion_steps_entry

    free_motion_velocity = float(free_motion_velocity_entry.get())
    free_motion_steps = int(free_motion_steps_entry.get())
    create_motion('z', 'forward', free_motion_steps, free_motion_velocity)
    update_current_position()


def free_move_backward():
    global free_motion_velocity_entry
    global free_motion_steps_entry

    free_motion_velocity = float(free_motion_velocity_entry.get())
    free_motion_steps = int(free_motion_steps_entry.get())
    create_motion('z', 'backward', free_motion_steps, free_motion_velocity)
    update_current_position()


def planned_x_movement(x_pos, x_vel):
    next_steps = calc_instructions_for_next_position(x_axis.get_values(), x_pos)

    if next_steps['direction'] == 1:
        direction = 'left'
    if next_steps['direction'] == 0:
        direction = 'right'

    create_motion('x', direction, next_steps['steps_amount'], x_vel)


def planned_y_movement(y_pos, y_vel):
    next_steps = calc_instructions_for_next_position(y_axis.get_values(), y_pos)

    if next_steps['direction'] == 1:
        direction = 'up'
    if next_steps['direction'] == 0:
        direction = 'down'

    create_motion('y', direction, next_steps['steps_amount'], y_vel)


def planned_z_movement(z_pos, z_vel):
    next_steps = calc_instructions_for_next_position(z_axis.get_values(), z_pos)

    if next_steps['direction'] == 1:
        direction = 'forward'
    if next_steps['direction'] == 0:
        direction = 'backward'

    create_motion('z', direction, next_steps['steps_amount'], z_vel)


def planned_movement():
    global x_position
    global x_velocity
    global y_position
    global y_velocity
    global z_position
    global z_velocity

    x_pos = float(x_position.get())
    y_pos = float(y_position.get())
    z_pos = float(z_position.get())

    x_vel = float(x_velocity.get())
    y_vel = float(y_velocity.get())
    z_vel = float(z_velocity.get())

    x_planned_thread = threading.Thread(target=planned_x_movement, args=(x_pos, x_vel,))
    y_planned_thread = threading.Thread(target=planned_y_movement, args=(y_pos, y_vel,))
    z_planned_thread = threading.Thread(target=planned_z_movement, args=(z_pos, z_vel,))
    x_planned_thread.start()
    y_planned_thread.start()
    z_planned_thread.start()
    x_planned_thread.join()
    y_planned_thread.join()
    z_planned_thread.join()
    update_current_position()
    # print(f'Current position: ({x_axis.current_position}, {y_axis.current_position}, {z_axis.current_position}) [mm]')


def clear_position():
    x_axis.current_position = 0.0
    y_axis.current_position = 0.0
    z_axis.current_position = 0.0
    update_current_position()


def exit_program():
    GPIO.cleanup()
    print("Bye bye.")
    exit()


GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

x_axis = Axis(axis_name='X axis', direction_pin=31, step_pin=29, kill_switch_i_pin=10,
              kill_switch_f_pin=11, direction='left', step_resolution=0.05, axis_length=1500)

y_axis = Axis(axis_name='Y axis', direction_pin=38, step_pin=40, kill_switch_i_pin=24,
              kill_switch_f_pin=27, direction='down', step_resolution=0.05, axis_length=500)

z_axis = Axis(axis_name='Z axis', direction_pin=8, step_pin=10, kill_switch_i_pin=23,
              kill_switch_f_pin=26, direction='forward', step_resolution=0.05, axis_length=2000)

master = Tk()
bg_color = 'white'
master.configure(bg=bg_color)
# master.attributes("-fullscreen", True)
s = ttk.Style()
s.theme_names()
('clam', 'alt', 'default', 'classic')
s.theme_use('clam')


current_position_value = (0, 0, 0)

master.title('Gantry controller V1.0')
master.resizable(width=True, height=True)
entry_width = 10
upper_text = 'Welcome to the gantry control panel.\n' \
             'All the positions are in [mm] and the velocities are in [mm/sec].\n\n' \
             "Go - Start motion to a specific point.\n" \
             "Home - Move the gantry to the system's origin.\n" \
             "Clear - Turns the current position into the system's origin.\n" \
             "\nThe free motion buttons will move the system freely \n" \
             "for a specified amount of steps in a specified velocity.\n" \
             "\n\nExit - Exit the program.\n\n"

Label(master, text=upper_text, anchor="n", justify=LEFT, bg=bg_color).grid(row=0, column=3, columnspan=3)

img = Image.open('download.png')
img = img.resize((170, 170))
img = ImageTk.PhotoImage(img)
panel = Label(master, image=img, anchor="e", justify=LEFT, bg=bg_color)
panel.grid(row=0, column=0, columnspan=3)
tab_text = "____________________________________________________________________________________________________\n " \
           "Planned motion\n"
Label(master, text=tab_text, anchor="n", justify=LEFT, bg=bg_color).grid(row=1, column=0, columnspan=5)

##### Position labels & buttons #####
Label(master, text="X position", bg=bg_color).grid(row=2, column=0)
x_position = Entry(master, width=entry_width)
x_position.grid(row=2, column=1, columnspan=1)
x_position.insert(END, '0')

Label(master, text="Y position", bg=bg_color).grid(row=3, column=0)
y_position = Entry(master, width=entry_width)
y_position.grid(row=3, column=1, columnspan=1)
y_position.insert(END, '0')

Label(master, text="Z position", bg=bg_color).grid(row=4, column=0)
z_position = Entry(master, width=entry_width)
z_position.grid(row=4, column=1, columnspan=1)
z_position.insert(END, '0')

##### Velocity labels & buttons #####
Label(master, text="    X velocity", bg=bg_color).grid(row=2, column=2)
x_velocity = Entry(master, width=entry_width)
x_velocity.grid(row=2, column=3, columnspan=1)
x_velocity.insert(END, '100')

Label(master, text="    Y velocity", bg=bg_color).grid(row=3, column=2)
y_velocity = Entry(master, width=entry_width)
y_velocity.grid(row=3, column=3, columnspan=1)
y_velocity.insert(END, '100')

Label(master, text="    Z velocity", bg=bg_color).grid(row=4, column=2)
z_velocity = Entry(master, width=entry_width)
z_velocity.grid(row=4, column=3, columnspan=1)
z_velocity.insert(END, '100')

ttk.Button(master, text='Go', command=planned_movement).grid(row=2, column=4)
ttk.Button(master, text='Home', command=homing_sequence).grid(row=3, column=4)
ttk.Button(master, text='Clear', command=clear_position).grid(row=4, column=4)

tab_text = "____________________________________________________________________________________________________\n " \
           "Free motion (20 steps = 1 [mm])\n"
Label(master, text=tab_text, anchor="n", justify=LEFT, bg=bg_color).grid(row=6, column=0, columnspan=5)
Label(master, text="Free motion buttons:", anchor="n", justify=LEFT, bg=bg_color).grid(row=7, column=0, columnspan=3)
Label(master, text="Free motion velocity:", anchor="n", justify=LEFT, bg=bg_color).grid(row=7, column=3, columnspan=1)
Label(master, text="Free motion steps amount:", anchor="n", justify=LEFT, bg=bg_color).grid(row=7, column=4,
                                                                                            columnspan=1)

free_motion_velocity_entry = Entry(master, width=entry_width)
free_motion_velocity_entry.insert(END, '500')
free_motion_velocity_entry.grid(row=8, column=3, columnspan=1)

free_motion_steps_entry = Entry(master, width=entry_width)
free_motion_steps_entry.insert(END, '100')
free_motion_steps_entry.grid(row=8, column=4, columnspan=1)

left = ttk.Button(master, text='Left', command=free_move_left)
left.grid(row=8, column=0)

right = ttk.Button(master, text='Right', command=free_move_right)
right.grid(row=9, column=0)
up = ttk.Button(master, text='Up', command=free_move_up)
up.grid(row=8, column=1)

down = ttk.Button(master, text='Down', command=free_move_down)
down.grid(row=9, column=1)

forward = ttk.Button(master, text='Forward', command=free_move_forward)
forward.grid(row=8, column=2)

backward = ttk.Button(master, text='Backward', command=free_move_backward)
backward.grid(row=9, column=2)

tab_text = "____________________________________________________________________________________________________\n"
Label(master, text=tab_text, anchor="n", justify=LEFT, bg=bg_color).grid(row=10, column=0, columnspan=5)
exit_button = ttk.Button(master, text='Exit', command=exit_program)
exit_button.grid(row=11, column=4, columnspan=1)

Label(master, text="Current position: ", anchor="n", justify=LEFT, bg=bg_color).grid(row=11, column=0, columnspan=2)
current_position_entry = Entry(master, width=20)
current_position_entry.insert(END, str(current_position_value))
current_position_entry.grid(row=11, column=1, columnspan=3)
Label(master, text="[mm]", anchor="n", justify=LEFT, bg=bg_color).grid(row=11, column=3, columnspan=1)

Label(master, text=tab_text, anchor="n", justify=LEFT, bg=bg_color).grid(row=12, column=0, columnspan=5)
mainloop()
