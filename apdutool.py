#!/usr/bin/env python3

# Python 2/3 compatability
try:
    import Tkinter
    from Tkinter import (
        Label,StringVar, Entry, OptionMenu, Frame, Menu, Toplevel,
        Button, Text, PanedWindow, Frame, Scrollbar, Checkbutton,
        IntVar, Radiobutton
    )
except:
    import tkinter as Tkinter
    from tkinter import (
        Label,StringVar, Entry, OptionMenu, Frame, Menu, Toplevel,
        Button, Text, PanedWindow, Frame, Scrollbar, Checkbutton,
        IntVar, Radiobutton
    )

from tkinter.scrolledtext import ScrolledText

import smartcard
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.CardConnection import CardConnection

import re
import itertools
import struct

class main_window(Tkinter.Tk):
    def __init__(self,parent):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.init_reader_globals()
        self.initialize()
    
    def init_reader_globals(self):
        self.selected_reader = StringVar()
        self.comm_mode = IntVar()
        self.reader = None
        self.output_data = []
    
    def _labels(self):
        pass
        #self.data_entry[i].bind("<Return>", self.OnPressEnter)
    
    def error(self, msg):
        error = Toplevel(self)
        Label(error, text="Error: " + msg).pack(padx=50, pady=30)
    
    def add_menubar(self):
        def print_val():
            print(self.selected_reader.get())
        
        def donothing():
            filewin = Toplevel(self)
            button = Button(filewin, text="Do nothing button", command=print_val)
            button.pack()
        
        def connect():
            try:
                self.connection = self.reader.createConnection()
                self.connection.connect(protocol=self.comm_mode.get())
                data = self.connection.getATR()
                data_string = ''.join(chr(n) for n in data if n > 31 and n < 128)
                self.ATR_display.set("ATR (Answer to Reset): {} | {}".format(toHexString(data),data_string))
                print(toHexString(data))
            except smartcard.Exceptions.CardConnectionException as e:
                self.error(e.message)
            except:
                self.error("You need to select a reader from Settings->Reader")
        
        def disconnect():
            try:
                self.connection.disconnect()
            except:
                self.error("No existing connection, or smartcard USB needs to be reset")
        
        def reconnect():
            disconnect()
            connect()
        
        def select_reader():
            def cancel():
                self.selected_reader.set(save_reader)
                self.comm_mode.set(save_comm_mode)
                win.destroy()
            
            def apply():
                _readers = readers()
                for i,r in enumerate(_readers):
                    if r.name == self.selected_reader.get():
                        self.reader = _readers[i]
                win.destroy()
            
            win = Toplevel(self)
            save_reader = self.selected_reader.get()
            save_comm_mode = self.comm_mode.get()
            Label(win, text="Reader: ").grid(row=0, column=0, sticky="w")
            OptionMenu(win, self.selected_reader, *readers()).grid(row=0, column=1, sticky="w")
            Label(win, text="Protocol: ").grid(row=1, column=0, sticky="w")
            Radiobutton(win, text="T = 0", variable=self.comm_mode, value=CardConnection.T0_protocol).grid(row=1,column=1,sticky="W")
            Radiobutton(win, text="T = 1", variable=self.comm_mode, value=CardConnection.T1_protocol).grid(row=2,column=1,sticky="W")
            Radiobutton(win, text="T = 0 or T = 1", variable=self.comm_mode, value=CardConnection.T15_protocol).grid(row=3,column=1,sticky="W")
            Radiobutton(win, text="T = RAW", variable=self.comm_mode, value=CardConnection.RAW_protocol).grid(row=4,column=1,sticky="W")
            Button(win, text="Cancel", command=cancel, width=15, bg="lightgrey").grid(row=5, column=0, sticky="E") 
            Button(win, text="Apply", command=apply, width=15, bg="lightgrey").grid(row=5, column=1, sticky="E") 
        
        menubar = Menu(self)
        
        filemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New", command=donothing)
        filemenu.add_command(label="Open", command=donothing)
        filemenu.add_command(label="Save", command=donothing)
        filemenu.add_command(label="Save as...", command=donothing)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        
        readermenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reader", menu=readermenu)
        readermenu.add_command(label="Connect", command=connect)
        readermenu.add_command(label="Reconnect", command=reconnect)
        readermenu.add_command(label="Disconnect", command=disconnect)
        readermenu.add_separator()
        readermenu.add_command(label="Status", command=donothing)
        
        settingsmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settingsmenu)
        settingsmenu.add_command(label="Reader Config", command=select_reader)
        
        helpmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command=donothing)
        
        self.config(menu=menubar)
    
    def add_byteinfo(self):
        self.labelorder = ["CLA", "INS", "P1", "P2", "Lc", "Le"]
        self.labelorder_desc = ["(1 byte) Instruction Class", "(1 byte) Instruction Code", "(1 byte) Instruction Parameter 1", "(1 byte) Instruction Parameter 2",
                                "(0-3 bytes) Number of command data bytes", "(0-3) Response Bytes Expected"]
        self.inputs = dict()
        self.data_entry = dict()
        self.byteinfo = Frame(self)
        
        for i,name in enumerate(self.labelorder):
            Label(self.byteinfo, text=name + ": ").grid(row=i+1, column=0, sticky="W")
            self.inputs[name] = StringVar()
            self.inputs[name].set(0)
            self.data_entry[name] = Entry(self.byteinfo, width=7, textvariable=self.inputs[name])
            #self.data_entry.append(OptionMenu(self, self.inputs[name], *range(0,256))) # This is a dropdown menu
            self.data_entry[name].grid(row=i+1, column=1,sticky="W")
            Label(self.byteinfo, text=self.labelorder_desc[i]).grid(row=i+1, column=2, sticky="W")
        
        self.byteinfo.grid(row=1, column=0, sticky="W")
    
    def add_inputoutput(self):
        pw = PanedWindow(self, background="darkgrey")
        #pw.pack(fill="both", expand=True)
        
        f1 = Frame(height=20, width=40)
        f2 = Frame(height=20, width=40)
        pw.add(f1)
        pw.add(f2)
        
        # Script box
        Label(f1, text="Command Data / script:").grid(row=0, column=0, sticky="sw")
        text = Text(f1, height=15, width=40, wrap="word")
        ysb = Scrollbar(f1, orient="vertical", command=text.yview)
        xsb = Scrollbar(f1, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        xsb.grid(row=2, column=0, sticky="ew")
        ysb.grid(row=1, column=1, sticky="ns")
        text.grid(row=1, column=0, sticky="nsew")
        
        self._input = text
        
        # Output box
        Label(f2, text="Response:").grid(row=0, column=0, sticky="W")
        text = Text(f2, height=15, width=40, wrap="word")
        ysb = Scrollbar(f2, orient="vertical", command=text.yview)
        xsb = Scrollbar(f2, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        xsb.grid(row=2, column=0, sticky="ew")
        ysb.grid(row=1, column=1, sticky="ns")
        text.grid(row=1, column=0, sticky="nsew")
        
        self._output = text
        
        f1.grid_rowconfigure(1, weight=1)
        f2.grid_rowconfigure(1, weight=1)
        f1.grid_columnconfigure(0, weight=1)
        f2.grid_columnconfigure(0, weight=1)
        
        pw.grid(column=0, row=4, rowspan=4, columnspan=8,sticky="NSEW", padx=10, pady=(1,4))
    
    def modify_bruteforce_custom_boxes(self):
        for name,data in self.bruteforce_check.iteritems():
            checked,custom,entry = data
            if checked.get():
                self.data_entry[name].configure(state="disabled")
                if custom.get():
                    entry.configure(state="normal")
                else:
                    entry.configure(state="disabled")
            else:
                self.data_entry[name].configure(state="normal")
                entry.configure(state="disabled")
    
    def modify_display(self):
        # self.mode is 0 in script mode, 1 in brute-force mode
        if self.mode.get() == 0:
            state = "disabled"
            for _,entry in self.data_entry.iteritems():
                entry.configure(state=state)
            for widget in self.bf_widgets:
                widget.configure(state=state)
            for _,_,label in self.bruteforce_check.values():
                label.configure(state=state)
        else:
            state = "normal"
            for _,entry in self.data_entry.iteritems():
                entry.configure(state=state)
            for widget in self.bf_widgets:
                widget.configure(state=state)
            self.modify_bruteforce_custom_boxes()
    
    def add_single_or_script(self):
        self.mode = IntVar()
        self.selectframe = Frame(self)
        Radiobutton(self.selectframe, text="Script Mode", variable=self.mode, value=0, command=self.modify_display).grid(row=0,column=0,sticky="W")
        Radiobutton(self.selectframe, text="Brute Mode", variable=self.mode, value=1, command=self.modify_display).grid(row=0,column=1,sticky="W")
        self.selectframe.grid(row=3, column=0, sticky="W")
    
    def add_bruteforce(self):
        # dict("CLA": [ checked 0|1 ,  All 0 | Custom 1 , Custom Entry])        
        self.bruteforce_check = dict()
        pw1 = PanedWindow(self, background="darkgrey")
        pw2 = PanedWindow(self, background="darkgrey")
        pw3 = PanedWindow(self, background="darkgrey")
        b1 = Frame(height=20, width=40)
        b2 = Frame(height=20, width=40)
        b3 = Frame(height=20, width=40)
        
        self.bf_ranges = dict()
        self.bf_widgets = []
        
        frames = [b1, b1, b2, b2, b3, b3]
        row_start = itertools.cycle([0,3])
        for i,name in enumerate(self.labelorder):
            row = row_start.next()
            self.bruteforce_check[name] = [IntVar(), IntVar()]
            self.bf_widgets.append(Checkbutton(frames[i], text="Bruteforce ({})".format(name), variable=self.bruteforce_check[name][0], command=self.modify_bruteforce_custom_boxes))
            self.bf_widgets[-1].grid(row=row, column=0, sticky="W")
            self.bf_widgets.append(Radiobutton(frames[i], text="All Bytes", variable=self.bruteforce_check[name][1], value=0, command=self.modify_bruteforce_custom_boxes))
            self.bf_widgets[-1].grid(row=row+1,column=0,sticky="W")
            self.bf_widgets.append(Radiobutton(frames[i], text="Custom", variable=self.bruteforce_check[name][1], value=1, command=self.modify_bruteforce_custom_boxes))
            self.bf_widgets[-1].grid(row=row+2,column=0,sticky="W")
            self.bf_ranges[name] = StringVar()
            self.bf_ranges[name].set(0)
            self.bruteforce_check[name].append(Entry(frames[i], width=16, textvariable=self.bf_ranges[name]))
            self.bruteforce_check[name][2].grid(row=row+2, column=1,sticky="W")
        
        pw1.add(b1)
        pw2.add(b2)
        pw3.add(b3)
        
        pw1.grid(row=1,column=1, sticky="NW")
        pw2.grid(row=1,column=2, sticky="NW")
        pw3.grid(row=1,column=3, sticky="NW")        
    
    def write(self, widget, text, clear=False):
        if clear:
            widget.delete("1.0",Tkinter.END)
        widget.insert(Tkinter.END, text)
    
    def do_bruteforce(self):
        def bruteforce_parse(name, r=None, get_input=True):
            if get_input:
                range_input = self.bf_ranges[name].get("1.0", Tkinter.END)
            else:
                range_input = r
            ret = set()
            singles = re.findall("[0-9a-f]{2}", range_input, re.IGNORECASE)
            ranges = re.findall("([0-9a-f]{2})-([0-9a-f]{2})", range_input, re.IGNORECASE)
            for val in singles:
                ret.add(int(val,16))
            for lo,hi in ranges:
                ret.update(list(range(int(lo,16), int(hi,16))))
            return ret

        # Looks like:   02 03 [5-10,18] [99]
        def parse_command(com):
            bytes = []
            tmp = com.split(" ")
            if len(tmp) < 1:
                return [[None]]
            for b in tmp:
                bytes.append(bruteforce_parse(None, b, False))
            return bytes
        
        def command_length(com_length):
            if com_length == 0: # Zero bytes
                print("command_length 0?")
            elif com_length < 0xff: # One byte
                return [com_length]
            else: # Three bytes
                bytes = [0]
                bytes.extend(struct.unpack("bb", struct.pack(">h", com_length)))
                return bytes

        checkbox = 0
        bfrange = 1
        allbytes = 0
        cla = set()
        ins = set()
        p1 = set()
        p2 = set()
        lc = set()
        le = set()
        ordered = [cla, ins, p1, p2, lc, le]
        for i,name in enumerate(self.labelorder):
            var = self.bruteforce_check[name]
            if var[checkbox].get():
                if var[bfrange].get() == allbytes:
                    ordered[i].update(list(range(0,256)))
                else:
                    ordered[i].update(bruteforce_parse(name))
            else:
                byte = self.inputs[name].get()
                print("Stringvar get: {}".format(byte))
                if byte.lower() == "x":
                    # Auto mode for Lc
                    ordered[i].update([None])
                else:
                    byte = int(byte, 16)
                    ordered[i].add(byte)

        command = self._input.get("1.0",Tkinter.END)
        command = parse_command(command)
        print("command after parse: {}".format(command))
        # command will look like: [set(0), set(3,30,33), set(0), set(0)]
        for line in itertools.product(cla, ins, p1, p2, lc, le):
            for com in itertools.product(*command):
                out = list(line[:4])
                if com[0] == None:
                    print("no command bytes?")
                    if le != None:
                        out.append(le)
                    self.send_apdu(out)
                else:
                    if line[4] == None:
                        out.extend(command_length(com))
                    else:
                        out.extend(command_length(line[4]))
                    out.extend(com)
                    if le != None:
                        out.append(le)
                    self.send_apdu(out)

    # Current limitations:
        # le can only be None or 00 (representing 256 bytes)
        # Auto mode for Lc is not in the gui
    def send_apdu(self, line):
        print("transmitting: {}".format(line))
        data, sw1, sw2 = self.connection.transmit(line)
        self.output_data.append(["%02x" % sw1, "%02x" % sw2, data])
        for sw1,sw2,data in self.output_data:
            # Todo: ASCII / Hex switch
            if True: # If HEX
                self.write(self._output, "Response Bytes: {} {}\nResponse Data: {}\n".format(sw1,sw2,data),True)
            else: # if ASCII
                tmp = ""
                for char in data:
                    tmp += chr(char) if (char > 31 or char < 128) else '.'
                self.write(self._output, "Response Bytes: {} {}\nResponse Data: {}\n".format(sw1,sw2,tmp),True)
   
    def execute(self):
        # Check if its in scripting mode first
        if self.mode.get():
            self.do_bruteforce()
        else:
            for line in self._input.get("1.0",Tkinter.END).split("\n"):
                line = [int(n,16) for n in line.split()]
                data, sw1, sw2 = self.connection.transmit(line)
                self.output_data.append(["%02x" % sw1, "%02x" % sw2, data])
        for sw1,sw2,data in self.output_data:
            # Todo: ASCII / Hex switch
            if True: # If HEX
                self.write(self._output, "Response Bytes: {} {}\nResponse Data: {}\n".format(sw1,sw2,data),True)
            else: # if ASCII
                tmp = ""
                for char in data:
                    tmp += chr(char) if (char > 31 or char < 128) else '.'
                self.write(self._output, "Response Bytes: {} {}\nResponse Data: {}\n".format(sw1,sw2,tmp),True)
    
    def initialize(self):
        self.grid()
        
        # Add menus
        self.add_menubar()
        
        # Blue top-display (status?)
        self.ATR_display = StringVar()
        Label(self,textvariable=self.ATR_display, anchor="w",fg="white",bg="blue").grid(column=0,row=0,columnspan=5,sticky='EW')
        self.ATR_display.set(u"ATR (Answer to Reset): ")
        
        # Make byte-info frame
        self.add_byteinfo()
        
        # Add bruteforcing options
        self.add_bruteforce()
        
        # Add mode select
        self.add_single_or_script()
        
        # Add Input/Output
        self.add_inputoutput()
        
        # Add Run button
        Button(self, text="Run", command=self.execute, width=15, bg="lightgrey").grid(row=3, column=0, sticky="E") 
        
        # Final grid set-up and display
        self.resizable(True,True)
        self.update()
        #self.geometry(self.geometry())       
        self.grid_columnconfigure(4,weight=1)
        self.grid_rowconfigure(4, weight=1)
        #self.entry.focus_set()
        #self.entry.selection_range(0, Tkinter.END)
        self.modify_display()
    
    def OnPressEnter(self,event):
        self.ATR_display.set( self.inputs["CLA"].get()+" (You pressed ENTER)" )
        #self.entry.focus_set()
        #self.entry.selection_range(0, Tkinter.END)

if __name__ == "__main__":
    app = main_window(None)
    app.title('APDUTool')
    app.mainloop()
