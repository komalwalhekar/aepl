'''
Copyright 2024-2025 Accolade Electronics Pvt. Ltd

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
version 2 as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

file        app_ui.py
brief       This is the source file for the GUI constructs

date        22 March 2024
author      Accolade Electronics <www.accoladeelectronics.com>
'''

import sys                      # for stdout
import tkinter as tk            # for core tk
import pandas as pd  # for handling Excel files
from datetime import datetime
import time
from PIL import Image, ImageTk 
from tkinter import ttk, filedialog, messagebox  
import app_comm
import app_logic


########################################### (GUI creation) ####################################################

class MyApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Accolade Service Tool')
        self.root.geometry('800x1000')  # Set window size to 800x1000
        self.create_widgets()  # Create widgets on window initialization

    def create_widgets(self):
        # Create a Notebook widget (tabs container)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Configuration Tab
        self.config_tab = tk.Frame(self.notebook)
        self.notebook.add(self.config_tab, text="Configuration")

        # Certificate Tab
        self.certificate_tab = tk.Frame(self.notebook)
        self.notebook.add(self.certificate_tab, text="Certificate")

        # Create the content for the Configuration Tab (from the previous code)
        self.create_configuration_tab_widgets()

        # Create the content for the Certificate Tab (empty for now)
        self.create_certificate_tab_widgets()

    def create_configuration_tab_widgets(self):
        self.main_frame = tk.Frame(self.config_tab, padx=20, pady=20)  # Padding for the main frame
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Upper row for logo, date/time, and utility name
        self.upper_frame = tk.Frame(self.main_frame, height=160, bg='sky blue')  # Set background color to sky blue
        self.upper_frame.pack(fill=tk.X)
        self.upper_frame.pack_propagate(False)  # Prevent frame from resizing based on its contents

        # Load and display the logo
        if not hasattr(self, 'logo_photo'):  # Check if the logo photo is already created
            try:
                logo_image = Image.open(r"Accolade Logo Without Background 3.png")  # Correct path to your logo
                logo_image = logo_image.resize((300, 150), Image.LANCZOS)  # Use Image.LANCZOS for resizing
                self.logo_photo = ImageTk.PhotoImage(logo_image)  # Keep a reference to avoid garbage collection
                print("Logo loaded successfully for Configuration tab.")
            except Exception as e:
                print(f"Error loading logo: {e}")
                self.logo_photo = None

        if self.logo_photo:  # Check if the logo was loaded successfully
            logo_label = tk.Label(self.upper_frame, image=self.logo_photo, bg='sky blue')  # Match background color
            logo_label.pack(side=tk.LEFT, padx=(10, 20))
        else:
            print("Logo not displayed in Configuration tab.")


        # Utility name
        utility_name = tk.Label(self.upper_frame, text="CONFIGURATION", font=("Times New Roman", 25, "bold"), bg='sky blue')  # Match background color
        utility_name.place(x=530, y=50)  # Set x and y coordinates as needed

        # Current date
        self.current_date = datetime.now().strftime("%Y-%m-%d")  # Format the date
        self.date_label = tk.Label(self.upper_frame, text=self.current_date, font=("Arial", 14), bg='sky blue')  # Match background color
        self.date_label.place(x=1150, y=60)  # Positioning below the utility name

        # Current time
        self.time_label = tk.Label(self.upper_frame, text="", font=("Arial", 14), bg='sky blue')  # Match background color
        self.time_label.place(x=1150, y=90)  # Positioning below the date

        # Call the method to update time
        self.update_time()

        # Create the lower frame to hold buttons and canvas (Excel content)
        self.lower_frame = tk.Frame(self.main_frame)
        self.lower_frame.pack(fill=tk.BOTH, expand=True, pady=20)  # Make the frame fill the space

        # Create a frame to hold the buttons horizontally
        button_frame = tk.Frame(self.lower_frame)
        button_frame.pack(side=tk.TOP, fill=tk.X)  # Align the button frame to the top with horizontal expansion

        # Load Excel File Button
        self.load_button = tk.Button(button_frame, text="Load Excel File", command=self.load_excel)
        self.load_button.pack(side=tk.LEFT, padx=40)  # Place this button on the left side of the button frame

        # Connect to CAN Bus Button, this button will be at the same y position as the "Load Excel File" button but different x position
        self.connect_button = tk.Button(button_frame, text="Connect to CAN Bus", command= app_logic.connect_to_can_bus )
        self.connect_button.pack(side=tk.LEFT, padx=200)  # Pack to the left with some padding

        # Read DIDs Button, this button will also be at the same y position as the "Load Excel File" button but different x position
        self.read_button = tk.Button(button_frame, text="Read DIDs", command= self.fire_dids)
        self.read_button.pack(side=tk.LEFT, padx=100)  # Place this button after the connect button with padding

        # Write DIDs Button
        self.write_button = tk.Button(button_frame, text="Write DIDs")
        self.write_button.pack(side=tk.LEFT, padx=100)  # Place this button after the connect button with padding

        # Add vertical space between the buttons and the loaded Excel content (canvas)
        spacer = tk.Frame(self.lower_frame, height=30)  # Create a spacer frame with height for vertical space
        spacer.pack(fill=tk.X)  # Pack the spacer to create space between the buttons and canvas

        # Create the canvas for the loaded Excel content
        self.canvas = tk.Canvas(self.lower_frame)
        self.scrollbar = tk.Scrollbar(self.lower_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        # Bind the scrollable frame to the canvas
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Pack the canvas and scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)


    def create_certificate_tab_widgets(self):
        # Create the main frame for the Certificate tab with padding
        self.main_frame = tk.Frame(self.certificate_tab, padx=20, pady=20)  # Padding for the main frame
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Upper row for logo, date/time, and tab name (Certificate)
        self.upper_frame = tk.Frame(self.main_frame, height=160, bg='sky blue')  # Set background color to sky blue
        self.upper_frame.pack(fill=tk.X)
        self.upper_frame.pack_propagate(False)  # Prevent frame from resizing based on its contents

        # Load and display the logo (use the same logo for consistency, or choose a different one)
        if not hasattr(self, 'logo_photo'):  # Check if the logo photo is already created
            try:
                logo_image = Image.open(r"Accolade Logo Without Background 3.png")  # Correct path to your logo
                logo_image = logo_image.resize((300, 150), Image.LANCZOS)  # Use Image.LANCZOS for resizing
                self.logo_photo = ImageTk.PhotoImage(logo_image)  # Keep a reference to avoid garbage collection
                print("Logo loaded successfully for Certificate tab.")
            except Exception as e:
                print(f"Error loading logo: {e}")
                self.logo_photo = None

        if self.logo_photo:  # Check if the logo was loaded successfully
            logo_label = tk.Label(self.upper_frame, image=self.logo_photo, bg='sky blue')  # Match background color
            logo_label.pack(side=tk.LEFT, padx=(10, 20))
        else:
            print("Logo not displayed in Certificate tab.")

        # Utility name for the Certificate tab
        certificate_name = tk.Label(self.upper_frame, text="CERTIFICATE", font=("Times New Roman", 25, "bold"), bg='sky blue')  # Match background color
        certificate_name.place(x=530, y=50)  # Set x and y coordinates as needed

        # Current date for the Certificate tab
        self.current_date = datetime.now().strftime("%Y-%m-%d")  # Format the date
        self.date_label = tk.Label(self.upper_frame, text=self.current_date, font=("Arial", 14), bg='sky blue')  # Match background color
        self.date_label.place(x=1150, y=60)  # Positioning below the utility name

        # Current time for the Certificate tab
        self.time_label = tk.Label(self.upper_frame, text="", font=("Arial", 14), bg='sky blue')  # Match background color
        self.time_label.place(x=1150, y=90)  # Positioning below the date

        # Call the method to update the time for the Certificate tab
        self.update_time()

        # Create the lower frame to hold file selection buttons
        self.lower_frame = tk.Frame(self.main_frame, padx=20, pady=20)
        self.lower_frame.pack(fill=tk.BOTH, expand=True, pady=20)  # Add vertical space

        # Add buttons for selecting 3 files
        self.select_button1 = tk.Button(self.lower_frame, text="Select File 1", command=lambda: self.select_file(1))
        self.select_button1.pack(pady=10)

        self.select_button2 = tk.Button(self.lower_frame, text="Select File 2", command=lambda: self.select_file(2))
        self.select_button2.pack(pady=10)

        self.select_button3 = tk.Button(self.lower_frame, text="Select File 3", command=lambda: self.select_file(3))
        self.select_button3.pack(pady=10)

        # Labels to display selected files
        self.file_label1 = tk.Label(self.lower_frame, text="No file selected", bg='sky blue')
        self.file_label1.pack(pady=5)

        self.file_label2 = tk.Label(self.lower_frame, text="No file selected", bg='sky blue')
        self.file_label2.pack(pady=5)

        self.file_label3 = tk.Label(self.lower_frame, text="No file selected", bg='sky blue')
        self.file_label3.pack(pady=5)

    def update_time(self):
        # Update the time label
        current_time = datetime.now().strftime("%H:%M:%S")  # Format the time
        self.time_label.config(text=current_time)  # Update label text
        self.time_label.after(1000, self.update_time)  # Call this method again after 1 second

    def load_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if file_path:
            try:
                # Read the Excel file
                df = pd.read_excel(file_path)
                # Extract UDS Parameter, DID, and Parameter Access columns
                self.parameters = df[['UDS Parameter', 'DID', 'Parameter Access']].dropna().values.tolist()
                self.display_parameters()
                self.dids = [str(did).strip() for did in df['DID'].dropna().values.tolist()]
                # Show a message box with the number of DIDs loaded
                messagebox.showinfo("DIDs Loaded", f"{len(self.dids)} DIDs loaded from the Excel file.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load Excel file: {e}")

    def display_parameters(self):
        # Clear previous widgets in the scrollable frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.entry_widgets = []  # Store references to Entry widgets

        # Create labels and text boxes in two columns
        for idx, (param, did, access) in enumerate(self.parameters):
            col = idx % 2  # 0 for the first column, 1 for the second column
            row = idx // 2  # Determine the row number

            param_label = tk.Label(self.scrollable_frame, text=param, width=30)
            param_label.grid(row=row, column=col * 4, sticky='w', padx=(5, 10), pady=5)

            did_label = tk.Label(self.scrollable_frame, text=did, width=20)
            did_label.grid(row=row, column=col * 4 + 1, sticky='w', padx=(5, 10), pady=5)

            text_box = tk.Entry(self.scrollable_frame, width=30)

            # Enable or disable the text box based on access
            if access == "Read":
                text_box.config(state='disabled', background='light gray')  # Disable and set light gray background
            elif access == "Read/Write":
                text_box.config(state='normal', background='white')

            text_box.grid(row=row, column=col * 4 + 2, sticky='ew', padx=(5, 10), pady=5)

            # Store the DID as an integer to avoid format issues
            did_value = int(did, 16)  # Convert DID from hex string to integer
            self.entry_widgets.append((did_value, text_box))  # Store the DID as an integer

            if col == 0:
                self.scrollable_frame.grid_columnconfigure(col * 4 + 3, minsize=50)  # Spacer column

        for col in range(8):
            self.scrollable_frame.grid_columnconfigure(col, weight=1)



    def fire_dids(self):
        if not hasattr(self, 'dids') or not self.dids:
            messagebox.showwarning("No DIDs", "No DIDs loaded. Please load an Excel file first.")
            return

        try:
            # Optionally, you can disable the button to prevent re-clicking while firing DIDs
            #self.read_did_button.config(state='disabled')

            # Fire each DID one by one with a delay of 5 seconds
            for did in self.dids:
                try:
                    # Convert DID from hex string to integer (if necessary)
                    did_int = int(did, 16)  # This converts the DID from string (hex) to integer
                    app_comm.test_read_write_did(app_comm.g_pcan_handle, app_comm.g_pcan_config, [did_int])
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid DID format: {did}. Error: {e}")
                    continue  # Skip this DID and move to the next one
                
                time.sleep(5)  # Wait for 5 seconds before firing the next DID

            # After all DIDs are fired, re-enable the button
            #self.read_did_button.config(state='normal')

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while firing DIDs: {e}")
            self.read_did_button.config(state='normal')
