#Square production script. Author: Giulio Peloso
#TO DO: fix warning "UUID già registrato" shows everytimes, even if the UUID is not present in the log file
#TO DO: add the check of the "seriale parlante"
#TO DO: close automatically the cmd window when the python gui is closed
#TO DO: when all the buttons are pressed go to the next phase without waiting for timeout
#TO DO: upcase the serial number

 # version 1.17 udated 21/02/2025: standyby instead of deep sleep at the end of the testing

import ...

# Load the TOML file
with open("settings.toml", "r") as file:
    settings = toml.load(file)

# File path to the text file
file_path = 'sap_log.txt'

# Define the address of your BLE device and the UUID of the characteristic
PRODUCER = settings['manufacturer']['producer']
CONTRACTOR = settings['manufacturer']['contractor']
WINDOW_BUTTON_PRESS = settings['manufacturer']['time_to_press_buttons']
SW_TESTING_VERSION = "0.1"
BLE_ADDRESS = ""  # Replace with your BLE device's address

SQUARE_BUTTONS_CHAR = "347b0045-7635-408b-8918-8ff3949ce592"

EEPROM_RESULT_NOTIFY = "347b0014-7635-408b-8918-8ff3949ce592" 
EEPROM_READ = "347b0013-7635-408b-8918-8ff3949ce592" 
EEPROM_WRITE = "347b0012-7635-408b-8918-8ff3949ce592" 
SQUARE_CONTROL_POINT = "347b0044-7635-408b-8918-8ff3949ce592"
EEPROM_READ_REQUEST =  0x0201000700
EEPROM_ANTID_WRITE_REQUEST =  bytearray(b'\x03\x01\x00\x02\x00')
EEPROM_HWVER_WRITE_REQUEST =  bytearray(b'\x03\x04\x00\x01\x00')
EEPROM_LOTNUM_WRITE_REQUEST =  bytearray(b'\x03\x06\x00\x01\x00')
EEPROM_PRODUCER_WRITE_REQUEST =  bytearray(b'\x03\x07\x00\x01\x00')


# Initialize the flag variable
flag_report = False

count_buttons_memory = [0] * 22
button_pressed = [0] * 22
out_button_pressed = [0] * 20
iteration = 0

button_event = Event()
global_flag = 0

def get_month_code():
    # Get the current date
    now = datetime.now()
    
    # List of letters corresponding to the months (A = January, B = February, etc.)
    month_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    # Get the current month (1 for January, 2 for February, etc.)
    current_month = now.month
    
    # Get the last two digits of the year
    year_suffix = str(now.year)[-2:]
    
    # Return the letter corresponding to the current month and year suffix
    return f"{month_letters[current_month - 1]}{year_suffix}"
    
def number_to_2_bytes(num):
    # Ensure the number is between 0 and 99999
    if num < 0 or num > 99999:
        raise ValueError("Number must be between 0 and 99999")
    
    # Fit the number into the range of 2 bytes (0 to 65535) using modulo
    num = num % 65536
    
    # Convert the number to 2 bytes (little-endian)
    byte_data = num.to_bytes(2, 'little')
    
    return byte_data

# Function to load the counter from the settings.toml file
def load_counter(config): 
    try:
        return int(config['device']['counter'])  # Read and return the stored value
    except (KeyError, ValueError):
        return 0  # If the file is invalid or missing the counter, start from 0

# Function to save the counter value to the settings.toml file
def save_counter(value):
        
    with open(file_path, 'r') as file:
        settings = toml.load(file)
    
    # Ensure 'device' section exists
    if 'device' not in settings:
        settings['device'] = {}
    
    settings['device']['counter'] = value  # Update the counter value
    
    # Write back to the settings.toml file
    with open(file_path, 'w') as file:
        toml.dump(settings, file)

def write_log(query_fields, filename='sap_log.txt'):
    # Check if the file exists and has content
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        # If file is new or empty, write the header
        with open(filename, 'w') as file:
            file.write(';'.join(query_fields) + '\n')


def find_rows_with_value(file_path, column_index, search_value):
    """
    Function to search for rows in a text file where a specific column contains a given value
    and the last column is "SUCCESS", excluding rows where the last column is "FAIL".
    
    Args:
    - file_path (str): Path to the text file.
    - column_index (int): The index of the column to search in (0-indexed).
    - search_value (str): The value to search for in the specified column.
    
    Returns:
    - matching_rows (list): A list of rows where the specified column contains the search value.
    """
    matching_rows = []
    
    # Open the file and read the data
    with open(file_path, newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';')  # Using ";" as delimiter
        for row in reader:
            # Skip empty or malformed rows
            if len(row) <= column_index:  
                continue
            
            # Check if the column matches the search value
            if row[column_index] == search_value:
                matching_rows.append(row)
    
    return matching_rows

def update_labels(array):
    for i in range(20):
        if array[i] > 0:
            labels[i].config(fg="green")
        else:
            labels[i].config(fg="red")

def set_labels_name():
    symbols = ["Ʌ","<","V",">","X","□","Bottone","Freno","Cambio1","Cambio2","Y","A","B","Z","●","▲","Bottone","Freno","Cambio1","Cambio2"]
    for i in range(20):            
        labels[i].config(text=symbols[i], fg="red")

def find_key_index(my_dict, key_to_find):
    try:
        # Convert the keys to a list and find the index
        keys_list = list(my_dict.keys())
        return keys_list.index(key_to_find)
    except ValueError:
        # If the key is not found, return -1 or some indication
        return -1  

async def scan_and_get_sorted_devices():
    # Scan for BLE devices
    scanner = BleakScanner()
    devices = await scanner.discover()

    # Sort devices by RSSI (signal strength)
    devices_sorted_by_rssi = sorted(devices, key=lambda d: d.rssi, reverse=True)

    # Return the sorted list of devices
    return devices_sorted_by_rssi

async def get_nearest_devices(type):
    devices = await scan_and_get_sorted_devices()
    devices = [device for device in devices if device.name == type]
    print(devices)
    return devices

async def read_ble_characteristic(address: str, characteristic_uuid: str) -> bytes:
    async with BleakClient(address) as client:
        value = await client.read_gatt_char(characteristic_uuid)
        return value

# Function to handle indications/notifications
def notification_handler(sender, data):

    print(f"Received data from {sender}: {data}")
    #print(f"Notification from {sender}: {data}")
    #self.update_label(f"Notification: {data}")
    global count_buttons_memory  # Declare that you want to use the global variable
    global button_pressed
    global out_button_pressed
    global iteration
    global global_flag

    # Initialize an empty list to store the split 4-bit values
    count_buttons = []

    # Loop through each byte in the bytearray
    for byte in data:
        # Extract the higher 4 bits by right-shifting by 4 and store in the list
        high_nibble = ( (byte) >> 4) & 0x0F
        count_buttons.append(high_nibble)
            
        # Extract the lower 4 bits by ANDing with 0x0F and store in the list
        low_nibble = (byte) & 0x0F
        count_buttons.append(low_nibble)

    # Output the result list
    if iteration > 0:
        result = [abs(a - b) for a, b in zip(count_buttons, count_buttons_memory)]
        button_pressed = [x + y for x, y in zip(button_pressed, result)]
        
        #format the array
        for i in range(len(button_pressed)):
            if button_pressed[i] > 1:
                button_pressed[i] = 1
                #self.update_label(f"Notification: {data}")
        out_button_pressed=button_pressed[2:]
        print(out_button_pressed)
        update_labels(out_button_pressed)

        # Check if all buttons are pressed
        if all(element == 1 for element in out_button_pressed):
            global_flag = 1
            button_event.set()  # Signal that all buttons are pressed

    iteration=iteration+1
    count_buttons_memory = count_buttons.copy()
    

def notification_eeprom(sender, data):
    print(f"Received data from {sender}: {data}")
    print("read/write eeprom")
    output_label.config(text="Lettura da eeprom") 

def is_valid_serial(serial: str) -> bool:
    """
    Check if the serial number is valid.
    
    A valid serial number:
    1. Starts with "SQ".
    2. Has a total length of 13 characters.
    
    Args:
        serial (str): The serial number to check.
    
    Returns:
        bool: True if the serial number is valid, False otherwise.
    """
    # Check if the string starts with "SQ" and has a length of 13
    return serial.startswith("SQ") and len(serial) == 13
    

# Add this function after is_valid_serial
def check_serial_and_update_button(*args):
    """
    Check if the serial number is valid and update the start button state.
    Called whenever the entry field changes.
    """
    if is_valid_serial(entry.get()):
        start_button.config(state=tk.NORMAL)
        entry.config(bg="white")
    else:
        start_button.config(state=tk.DISABLED)
        entry.config(bg="pink")  # Visual feedback for invalid input

async def async_operation():
    #global BLE_ADDRESS
    global out_button_pressed

    user_input = entry.get()
    #if is_valid_serial(user_input):
    output_label.config(text="Connessione in corso, attendere")
    #find Square devices near
    device_type = "SQUARE"
    Squares = await get_nearest_devices(device_type)
    ble_address = 0
    if Squares:
        ble_address = Squares[0]
        #BLE_ADDRESS = ble_address.address
        print(f"ble address:{ble_address.address}")
        #print(type(BLE_ADDRESS))
    else:
        print("No Square near you")  
        #self.update_label("No Square near you")    
        return "Nessun dispositivo trovato"

    output_label.config(text="Dispositivo trovato, attendere!")

    #ble_address_test = "FE:A1:4A:D0:4B:AF"
    print(f"device found:{ble_address.address}")
    async with BleakClient(ble_address.address, timeout=30.0) as client:
        global flag_report
        ant_id = -1           
        # Ensure that the client is connected
        if client.is_connected: 
            output_label.config(text="Connesso con successo")

            # CHECK BUTTONS
            await client.start_notify(SQUARE_BUTTONS_CHAR, notification_handler)
            output_label.config(text="Premere tutti i pulsanti entro il timeout")

            # Reset event and flag before starting
            button_event.clear()
            global global_flag
            global_flag = 0

            # Wait to receive indications (for demonstration, we'll wait for 30 seconds)            
            try:
                # Wait for event with timeout
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: button_event.wait(timeout=WINDOW_BUTTON_PRESS)
                )
            except asyncio.TimeoutError:
                print("Timeout reached")
                global_flag = 1

            # Stop notifications/indications
            await client.stop_notify(SQUARE_BUTTONS_CHAR)

            #if True:
            if all(element == 1 for element in out_button_pressed):                    
                set_green_buttons_indicator()

                # Define the query fields
                query_fields = [
                    'Date', 'Time', 'self-expl-ID','ANT-SN', 
                    'FWVersion', 'HWVersion', 'SW_Testing', 'Batch', 
                    'Producer', 'Contractor', 'BLE-addr'
                ]

                # Create the query dictionary using query_fields
                query = {field: None for field in query_fields}

                # Call the function to write to the log file (only if new or empty)
                log_file_path = 'sap_log.txt'            
                write_log(query_fields, log_file_path)
                
                query['SW_Testing']=SW_TESTING_VERSION
                
                query['Contractor'] = CONTRACTOR               
                query['BLE-addr'] = BLE_ADDRESS                        
                query['Date']=datetime.now().strftime("%d/%m/%Y")
                query['Time']=datetime.now().strftime("%H.%M.%S")
    
                        
                query['self-expl-ID']= user_input       
                
                sw_version = await client.read_gatt_char("2A28")
                query['FWVersion']= sw_version.decode('utf-8')
                
                # Subscribe to notifications/indications
                await client.start_notify(EEPROM_RESULT_NOTIFY, notification_eeprom)
                
                
                #write Batch (numero lotto) number from toml
                await client.write_gatt_char(EEPROM_RESULT_NOTIFY, bytearray([0x03]))
                lot_id = settings['manufacturer']['batch']
                lot_id_in_byte = lot_id.to_bytes(1, byteorder='big')
                await client.write_gatt_char(EEPROM_WRITE, EEPROM_LOTNUM_WRITE_REQUEST + lot_id_in_byte )            
                query['Batch'] = lot_id

                #write producer number from toml
                await client.write_gatt_char(EEPROM_RESULT_NOTIFY, bytearray([0x03]))
                producer_id = PRODUCER
                producer_id_byte = producer_id.to_bytes(1, byteorder='big')
                await client.write_gatt_char(EEPROM_WRITE, EEPROM_PRODUCER_WRITE_REQUEST + producer_id_byte )
                query['Producer'] = producer_id  


                #write HW version from toml
                await client.write_gatt_char(EEPROM_RESULT_NOTIFY, bytearray([0x03]))
                hwversion_int =settings['device']['hw_version']
                hwversion_in_byte = hwversion_int.to_bytes(1, byteorder='big')
                await client.write_gatt_char(EEPROM_WRITE, EEPROM_HWVER_WRITE_REQUEST + hwversion_in_byte )


                await client.stop_notify(EEPROM_RESULT_NOTIFY)


                #read ant id via BLE read
                ant_id_from_char = await client.read_gatt_char("2A25")
                query['ANT-SN'] = int(ant_id_from_char)
                print(f"ant id : {int(ant_id_from_char)}") 

                #read hw version
                hwver_from_char = await client.read_gatt_char("2A27")
                
                #TO DO: read ant_id from BLE and add check if matches or not
                if( int(hwver_from_char.decode('utf-8')) == hwversion_int ):
                    
                    query['HWVersion'] = hwversion_int
                    # File path to the text file
                    file_path = 'sap_log.txt'
                    search_item_1 = query['self-expl-ID']
                    search_column_1 = "self-expl-ID"
                    search_item_2 = BLE_ADDRESS
                    search_column_2 = "BLE-addr"
                    search_result_1 = None
                    search_result_2 = None
                    try:
                        if os.path.exists(file_path):
                            column_index1 = find_key_index(query,search_column_1)                
                            search_result_1 = find_rows_with_value(file_path, column_index1, search_item_1)                    
                            column_index2 = find_key_index(query,search_column_2)                
                            search_result_2 = find_rows_with_value(file_path, column_index2, search_item_2)

                        if( search_result_1 ):
                            output_label.config(text="ATTENZIONE: Seriale parlante gia' registrato !", fg="red")
                            time.sleep(2)
                            output_label.config(text=" ", fg="black")

                        #TO DO: fix warning "UUID già registrato" shows everytimes, even if the UUID is not present in the log file (disabled for the moment)
                        #if( search_result_2 ):
                            #output_label.config(text="ATTENZIONE: UUID gia' registrato !", fg="red")
                            #time.sleep(2)
                            #output_label.config(text=" ", fg="black")
                    except:
                        print("exception in searching value in reading log data")

                    set_green_report_indicator()
                    
                    # Open the file in write mode
                    with open('sap_log.txt', 'a') as file:  # Open the file in append mode
                        # Write all values in a single line, separated by a space
                        file.write(';'.join(str(value) for value in query.values()) + '\n')  # Add a newline character to write on a new line

                else:
                    print("error: inconsistency between eeprom and ble data")
                    set_red_report_indicator()
                    output_label.config(text="error: inconsistency between eeprom and ble data", fg="red")
                    time.sleep(3)
                    output_label.config(text=" ", fg="black")
                    
                
                
                
            else:
                output_label.config(text="Fallimento: pulsanti non funzionano !", fg="red")
                time.sleep(3)
                output_label.config(text=" ", fg="black")
                print("Fail: buttons not working !")                
                set_red_report_indicator()
                set_red_buttons_indicator()

            #Turn off Square                     
            output_label.config(text="Spegnimento Square...")   
            print("Turning off square...")               
            await client.write_gatt_char(SQUARE_CONTROL_POINT, bytearray([0x0A, 0x00]), response=False) # 0x01 shout down, 0x00 sleep


            #UPDATE THE COUNTER
            # Path to the TOML file
            toml_file_path = 'settings.toml'

            # Load the current TOML settings
            with open(toml_file_path, 'r') as file:
                config = toml.load(file)

            # Print the current config (optional)
            print("Before update:", config)

            
            # Write the updated settings back to the TOML file
            with open(toml_file_path, 'w') as file:
                toml.dump(config, file)

            print("After update:", config)            
            

            return "Fine"
        else:
            return "Connessione BLE fallita"
  
    
    
            

# Function to start the async operation
def start_operation():
    output_label.config(text="Start")
    start_button.config(state=tk.DISABLED)
    set_grey_report_indicator()
    set_grey_buttons_indicator()

    # Run the async operation in a separate thread to avoid blocking the main thread
    main_thread = threading.Thread(target=run_async_operation).start()
    

def run_async_operation():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(async_operation())
    output_label.config(text=result)

# Function to restart the output label
def start_connection():    
    output_label.config(text="Start !")

def restart():
    """
    Restarts the entire Python program.
    """
    python = sys.executable  # Path to the Python interpreter
    os.execl(python, python, *sys.argv)  # Restart the program with the same arguments

# Function to restart the output label
def close():    
    root.destroy()  # Close the current Tkinter window

def set_red_report_indicator():
    canvas2.itemconfig(report_indicator, fill="red")

def set_green_report_indicator():
    canvas2.itemconfig(report_indicator, fill="green")

def set_red_buttons_indicator():
    canvas.itemconfig(buttons_indicator, fill="red")

def set_green_buttons_indicator():
    canvas.itemconfig(buttons_indicator, fill="green")

def set_grey_report_indicator():
    canvas2.itemconfig(report_indicator, fill="grey")

def set_grey_buttons_indicator():
    canvas.itemconfig(buttons_indicator, fill="grey")


# Creating the main window
root = tk.Tk()
root.title("Square testing")
root.geometry('1100x650')

# Create a label with bigger font
label1 = tk.Label(root, text="Messaggio: 🡒", font=("Arial", 12))
label1.grid(row=0, column=0, padx=1, pady=1)

# Creating the output label
output_label = tk.Label(root,
                        text="",
                        bg="lightblue",
                        font=("Arial", 14),
                        padx=15,               
                        pady=15,                
                        justify=tk.CENTER,                           
                        underline=0,           
                        wraplength=250         
                        )

# Pack the label into the window
output_label.grid(row=0, column=1, padx=1, pady=1)  # Place the label in row 0, column 0

# Create a label with bigger font
label_id_counter = tk.Label(root, text="Seriale parlante 🡒", font=("Arial", 12))
label_id_counter.grid(row=1, column=0, padx=1, pady=1)  

# Load the initial counter value from the settings.toml file
initial_value = load_counter(settings) #to ceck if the counter is needed
# Access data from the TOML file
print(settings)
# Create an entry (input text box) with the loaded value
entry = tk.Entry(root, width=16)
entry.grid(row=1, column=1, padx=1, pady=1)
#entry.insert(0, "SQ"+ get_month_code() + str(initial_value).zfill(4))  # Set the initial value in the entry box
# Set focus on the Entry widget when the application opens
entry.focus_set()

# Add trace to entry widget to monitor changes
entry.bind('<KeyRelease>', lambda e: check_serial_and_update_button())

# Create a label with bigger font
label_hw_version = tk.Label(root, text="HW Version =", font=("Arial", 12))
label_hw_version.grid(row=2, column=0, padx=1, pady=1)  

hw_version_text = str(settings['device']['hw_version'])
# Creating the output label
hw_version_label = tk.Label(root,
                        text=hw_version_text,
                        font=("Arial", 11 ),
                        padx=5,               
                        pady=10,                
                        justify=tk.CENTER,    
                        wraplength=250         
                        )

# Pack the label into the window
hw_version_label.grid(row=2, column=1, padx=1, pady=1)  # Place the label in row 0, column 0

# Creating the start button
start_button = tk.Button(root, text="Start", command=start_operation, bg="lightblue", state=tk.DISABLED)
start_button.grid(row=3, column=0, padx=1, pady=1)  # Place the label in row 0, column 0

# Create a label with bigger font
label2 = tk.Label(root, text="Pulsanti 🡒", font=("Arial", 12))
label2.grid(row=5, column=0, padx=1, pady=1)  
                        
# Create a canvas for the indicator
canvas = tk.Canvas(root, width=100, height=100)
canvas.grid(row=5, column=1, padx=1, pady=1)  # Place the canvas in row 0, column 1 next to the label
# Create a circle (indicator) on the canvas
buttons_indicator = canvas.create_oval(20, 20, 80, 80, fill="grey")

# Create a label with bigger font
label3 = tk.Label(root, text="Non dimenticare di testare i LED!", font=("Arial", 12))
label3.grid(row=6, column=0, padx=1, pady=1)  

# Create a canvas for the indicator
canvas2 = tk.Canvas(root, width=100, height=100)
canvas2.grid(row=7, column=1, padx=1, pady=1)  # Place the canvas in row 0, column 1 next to the label
report_indicator  = canvas2.create_oval(20, 20, 80, 80, fill="grey")


# Create a label with bigger font
label3 = tk.Label(root, text="Report 🡒", font=("Arial", 12))
label3.grid(row=7, column=0, padx=1, pady=1)  

# Creating the restart button
restart_button = tk.Button(root, text="Restart", command=restart)
restart_button.grid(row=9, column=0, padx=1, pady=2)  # Place the label in row 0, column 0



# Create labels to display each item status
labels = []
for i in range(20):
    col = 2 + i // 10  # Determines the column (0 for first 10, 1 for the rest)
    row =   i % 10   # Determines the row (0-9) + 1 to avoid overlap with the button
    label = tk.Label(root, text="", font=("Arial", 16, "bold"), width=20)
    label.grid(row=row, column=col, padx=1, pady=1)
    labels.append(label)

# Initial update of labels with a list of zeros
update_labels([0] * 20)
set_labels_name()

# Running the Tkinter event loop
root.mainloop()