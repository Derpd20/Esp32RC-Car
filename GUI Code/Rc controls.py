import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import serial.tools.list_ports
import pygame
import threading
import time

pygame.init()
pygame.joystick.init()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gamepad Serial Controller")

        self.serial_port = None
        self.serial_thread = None
        self.serial_running = False
        self.joystick = None
        self.joystick_index = 0

        # UI Variables
        self.gamepad_var = tk.StringVar()
        self.port_var = tk.StringVar()
        self.last_packet_var = tk.StringVar(value="None")

        # Layout
        self.create_widgets()
        self.refresh_devices()
        self.root.after(50, self.update_joystick_display)

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        # Gamepad selector
        ttk.Label(frame, text="Gamepad:").grid(row=0, column=0, sticky="w")
        self.gamepad_combo = ttk.Combobox(frame, textvariable=self.gamepad_var, state="readonly", width=60)
        self.gamepad_combo.grid(row=0, column=1)
        self.gamepad_combo.bind("<<ComboboxSelected>>", self.select_gamepad)

        # Port selector
        ttk.Label(frame, text="Serial Port:").grid(row=1, column=0, sticky="w")
        self.port_combo = ttk.Combobox(frame, textvariable=self.port_var, state="readonly", width=60)
        self.port_combo.grid(row=1, column=1)

        # Refresh + Connect/Disconnect
        ttk.Button(frame, text="Refresh", command=self.refresh_devices).grid(row=0, column=2)
        self.connect_btn = ttk.Button(frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=1, column=2)

        # Joystick position
        ttk.Label(frame, text="Joystick Position:").grid(row=2, column=0, sticky="w")
        self.joystick_label = ttk.Label(frame, text="X: 0.00, Y: 0.00, Btn: []")
        self.joystick_label.grid(row=2, column=1, columnspan=2, sticky="w")

        # Last Packet Sent
        ttk.Label(frame, text="Last Sent Packet:").grid(row=3, column=0, sticky="w")
        self.last_packet_label = ttk.Label(frame, textvariable=self.last_packet_var)
        self.last_packet_label.grid(row=3, column=1, columnspan=2, sticky="w")

        # Serial Monitor
        ttk.Label(frame, text="Serial Output:").grid(row=4, column=0, sticky="nw")
        self.serial_output = scrolledtext.ScrolledText(frame, height=10, width=60, state="disabled")
        self.serial_output.grid(row=4, column=1, columnspan=2)

    def refresh_devices(self):
        # Gamepads
        pygame.joystick.quit()
        pygame.joystick.init()
        gamepads = [pygame.joystick.Joystick(i).get_name() for i in range(pygame.joystick.get_count())]
        self.gamepad_combo['values'] = gamepads
        if gamepads:
            self.gamepad_combo.current(0)
            self.select_gamepad()

        # Serial ports
        ports = serial.tools.list_ports.comports()
        values = []
        self.port_map = {}
        for port in ports:
            desc = f"{port.device} ({port.description})"
            values.append(desc)
            self.port_map[desc] = port.device
        self.port_combo['values'] = values
        if values:
            self.port_combo.current(0)

    def select_gamepad(self, event=None):
        index = self.gamepad_combo.current()
        if index != -1:
            self.joystick = pygame.joystick.Joystick(index)
            self.joystick.init()

    def toggle_connection(self):
        if self.serial_running:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        try:
            port_desc = self.port_var.get()
            port = self.port_map[port_desc]
            self.serial_port = serial.Serial(port, 115200, timeout=0.1)
            self.serial_running = True
            self.connect_btn.config(text="Disconnect")
            self.serial_thread = threading.Thread(target=self.read_serial_loop, daemon=True)
            self.serial_thread.start()
        except Exception as e:
            self.append_serial(f"Connection failed: {e}")

    def disconnect_serial(self):
        self.serial_running = False
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
        self.connect_btn.config(text="Connect")

    def read_serial_loop(self):
        while self.serial_running and self.serial_port:
            try:
                line = self.serial_port.readline().decode(errors='ignore').strip()
                if line:
                    self.append_serial(f"[RX] {line}")
            except:
                pass
            time.sleep(0.05)

    def send_packet(self, packet: bytes):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(packet)
            self.last_packet_var.set(" ".join(f"{b:02X}" for b in packet))

    def append_serial(self, text):
        self.serial_output.configure(state="normal")
        self.serial_output.insert(tk.END, text + "\n")
        self.serial_output.see(tk.END)
        self.serial_output.configure(state="disabled")

    def update_joystick_display(self):
        if self.joystick:
            pygame.event.pump()
            x = round(self.joystick.get_axis(0), 2)
            y = round(self.joystick.get_axis(1), 2)
            buttons = [i for i in range(self.joystick.get_numbuttons()) if self.joystick.get_button(i)]
            self.joystick_label.config(text=f"X: {x:.2f}, Y: {y:.2f}, Btn: {buttons}")

            # Example packet structure
            throttle = int((1 - y) * 127.5)  # 0-255, reversed Y axis
            direction = 1 if y < 0 else 0
            steer = int((x + 1) * 127.5)

            # Format: 0xFF, len, id, val, ..., '\n'
            packet = bytes([0xFF, 6, 1, throttle, 2, direction, 3, steer]) + b'\n'
            self.send_packet(packet)

        self.root.after(50, self.update_joystick_display)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
