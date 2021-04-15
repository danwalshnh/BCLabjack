from tkinter import *
#from ljf import run_labjack
import datetime

from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
from ljf import run_labjack

class LJGui:

    def __init__(self):
        self.myGui = Tk()

        self.myGui.title("Balance Community LabJack Processor")
        self.myGui.geometry("600x200+700+200")
        load = Image.open("logo.png")
        load_resized = load.resize((200, 25), Image.ANTIALIAS)
        render = ImageTk.PhotoImage(load_resized)
        img = Label(self.myGui, image=render)
        img.image = render
        img.place(x=0, y=0)

        myLabel = Label(text="Welcome! Enter the max number of requests, directory to save output and press run:",fg="blue",justify='left')


        self.MAX_REQUEST= IntVar()
        self.MAX_REQUEST_OUTPUT = str(self.MAX_REQUEST)
        self.directory = StringVar()
        self.path = StringVar()
        self.output= StringVar()

        self.finalMax = Label(textvariable = self.MAX_REQUEST_OUTPUT,fg='red',justify='left').place(x=150,y=60)
        self.finalSaveTo= Label(textvariable = self.directory,fg='red',justify='left').place(x=150,y=90)
        self.finalRun = Label(textvariable = self.path, fg = 'red',justify='left').place(x=150,y=120)


        MaxEntry = Entry(self.myGui, textvariable =  self.MAX_REQUEST,justify='center').place(x=10,y=60)

        SaveToButton = Button(text = "Save to", command = self.SaveTo).place(x=10,y=90)
        RunButton = Button(text = "Run", command = self.Run).place(x=10,y=120)
        reset = Button(text = "Reset Values", command = self.reset_values).place(x=10,y=165)

        quit = Button(text="Quit", command = self.closeWin).place(x=385,y=165)

        self.myGui.mainloop()



    def SaveTo(self):
        self.directory.set(filedialog.askdirectory(initialdir='/'))



    def Run(self):
        self.path.set(str(self.directory.get()) + '/' + datetime.datetime.now().strftime(format='%Y-%m-%d_%H-%M-%S') + '-log.csv')
        try:
            with open(self.path.get(), "w") as file:
                file.write('time,measurement\n')
                i = 0
                while i <= self.MAX_REQUEST.get():
                    file.write(str(i) + "," + str(i * 3)+'\n')
                    i+=1
                #run_labjack(file, MAX_REQUEST)
            self.output.set("Success")
        except Exception as e:
            self.output.set(str(e))




    def closeWin(self):
        self.myGui.destroy()                   #Close Window Function


    def reset_values(self):
        self.MAX_REQUEST.set(0)
        self.directory.set('')
        self.path.set('')
        self.output.set('')
