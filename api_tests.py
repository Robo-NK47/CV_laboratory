from tkinter import *


def print_text():
    global e
    string = e.get()
    print(string)


root = Tk()

root.title('Name')

e = Entry(root)
e.pack()
e.focus_set()

b = Button(root, text='okay', command=print_text)
b.pack(side='bottom')
root.mainloop()
