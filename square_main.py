"""
@main Square production script
@brief Python project used in production for testing and configuring Square products

@update 2025-02-21
@note Completely fixed the first version of the test program

@author Samuel Fior
@date 2025-07-29
@version 1.0.0.0
"""


#######################################################################################################################
# IMPORT
#######################################################################################################################
import tomli
import tomli_w
import time
import sys
import os
import asyncio
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from threading import Event
from datetime import datetime
from bleak import BleakScanner, BleakClient

#######################################################################################################################
# MACRO AND GLOBAL VARIABLES
#######################################################################################################################
# Software version
SW_TESTING_VERSION = "1.0.0.0"

# Bluetooth Services
UUID_EEPROM_WRITE = "347b0012-7635-408b-8918-8ff3949ce592"
UUID_EEPROM_READ = "347b0013-7635-408b-8918-8ff3949ce592"
UUID_EEPROM_RESULT = "347b0014-7635-408b-8918-8ff3949ce592"
SQUARE_BUTTONS_CHAR = "347b0045-7635-408b-8918-8ff3949ce592"
SQUARE_CONTROL_POINT = "347b0044-7635-408b-8918-8ff3949ce592"

# Bluetooth request sequences
EEPROM_ANTID_WRITE_REQUEST = bytearray(b'\x03\x01\x00\x02\x00')
EEPROM_HWVER_WRITE_REQUEST = bytearray(b'\x03\x04\x00\x01\x00')
EEPROM_BATCH_WRITE_REQUEST = bytearray(b'\x03\x06\x00\x01\x00')
EEPROM_PRODUCER_WRITE_REQUEST = bytearray(b'\x03\x07\x00\x01\x00')
EEPROM_ANTID_READ_REQUEST = bytearray(b'\x02\x01\x00\x02\x00')
EEPROM_HWVER_READ_REQUEST = bytearray(b'\x02\x04\x00\x01\x00')
EEPROM_BATCH_READ_REQUEST = bytearray(b'\x02\x06\x00\x01\x00')
EEPROM_PRODUCER_READ_REQUEST = bytearray(b'\x02\x07\x00\x01\x00')

# External file paths
toml_file_path = 'settings.toml'
log_file_path = 'sap_log.txt'

# List of valid colours used in Canvas Lib
ValidColours = ["grey", "green", "red"]
# List of buttons to check
symbols = ["Ʌ", "<", "V", ">", "X", "■", "Bottone SX", "Freno SX", "Cambio1 SX", "Cambio2 SX",
           "Y", "A", "B", "Z", "●", "▲", "Bottone DX", "Freno DX", "Cambio1 DX", "Cambio2 DX"]

# Producer dictionary
producers = [
    {
        "name": "Default",
        "internal_code": 0
    },
    {
        "name": "Ceis",
        "internal_code": 1
    },
    {
        "name": "Pimas",
        "internal_code": 2
    },
    {
        "name": "Dea",
        "internal_code": 3
    },
    {
        "name": "Elettrodue",
        "internal_code": 4
    }
]
# Manufacturer dictionary
manufacturers = [
    {
        "name": "Default",
        "internal_code": 0
    },
    {
        "name": "Brotto",
        "internal_code": 1
    },
    {
        "name": "Cosmo",
        "internal_code": 2
    },
    {
        "name": "Elite",
        "internal_code": 3
    },
    {
        "name": "Clone",
        "internal_code": 4
    }
]
# Elite devices dictionary
elite_devices = [
    {
        "name": "ARIA",
        "sn_code": "AI",
        "sn_length": 13
    },
    {
        "name": "AVANTI",
        "sn_code": "AV",
        "sn_length": 13
    },
    {
        "name": "DIRETO XR",
        "sn_code": "XR",
        "sn_length": 13
    },
    {
        "name": "DIRETO XR-T",
        "sn_code": "XR",
        "sn_length": 13
    },
    {
        "name": "FUORIPISTA",
        "sn_code": "FP",
        "sn_length": 13
    },
    {
        "name": "GATEWAY",
        "sn_code": "GW",
        "sn_length": 13
    },
    {
        "name": "JUSTO",
        "sn_code": "JU",
        "sn_length": 13
    },
    {
        "name": "JUSTO 2",
        "sn_code": "J2",
        "sn_length": 13
    },
    {
        "name": "NERO",
        "sn_code": "NE",
        "sn_length": 13
    },
    {
        "name": "RIVO",
        "sn_code": "RV",
        "sn_length": 13
    },
    {
        "name": "RIZER",
        "sn_code": "RZ",
        "sn_length": 13
    },
    {
        "name": "SQUARE",
        "sn_code": "SQ",
        "sn_length": 13
    },
    {
        "name": "STERZO SMART",
        "sn_code": "ST",
        "sn_length": 13
    },
    {
        "name": "SUITO",
        "sn_code": "SU",
        "sn_length": 13
    },
    {
        "name": "SUITO - T",
        "sn_code": "SU",
        "sn_length": 13
    },
    {
        "name": "TUO",
        "sn_code": "TO",
        "sn_length": 13
    },
    {
        "name": "TURNO",
        "sn_code": "TU",
        "sn_length": 13
    },
    {
        "name": "ZONA",
        "sn_code": "ZN",
        "sn_length": 7
    },
    {
        "name": "ZUMO",
        "sn_code": "ZU",
        "sn_length": 13
    }
]

# Auxiliary variables
count_buttons_memory = [0] * 22
button_pressed = [0] * 22
out_button_pressed = [0] * 20
iteration = 0
flag_exit = False
button_event = Event()
status_ok = True
first_test = True

# Imported variables from settings.toml file
PRODUCER = 0
PROD_BATCH = 0
TARGET_NAME = ""
HW_VERSION = 0
ANT_ID = 0
RSSI_MIN = 0
SCAN_TIMEOUT = 0.0
BLE_TIMEOUT = 0.0
TEST_TIME = 0
MANUFACTURER = ""
SETT_FILE_VER = 0.0
FINAL_TEST = ""
settings = {}


#######################################################################################################################
# FUNCTIONS
#######################################################################################################################

def get_crc_16(data: bytes) -> int:
    """
    @description: Calculates the CRC-16 checksum for a given byte sequence.

    @param data: The input data to process, provided as a sequence of bytes.

    @return crc: The computed CRC-16 value as an integer.
    """
    global editor
    crc = 0

    try:
        # Calculate CRC value
        for i in data:
            crc ^= i
            for j in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0x6C49
                else:
                    crc = crc >> 1

        # Return calculated CRC value
        return crc

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante get_crc_16(): {e}\n\n", "red")


def crc16_from_str(input_str: str) -> int:
    """
    @description: Converts a UTF-8 string into bytes and computes its CRC-16 checksum.

    @param input_str: The input string to be encoded and processed.

    @return get_crc_16(data): The CRC-16 checksum of the encoded byte representation of the string.
    """
    global editor

    try:
        # Convert string to bytes
        data = input_str.encode('utf-8')

        return get_crc_16(data)

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante crc16_from_str(): {e}\n\n", "red")


def create_gui() -> None:
    """
    @description: Initializes and displays the main graphical user interface for the testing application. It creates
                  input fields, fixed labels, test indicators, action buttons, and the editor panel.
    """
    global root, frame_sx, frame_editor, frame_buttons, saved_label_row, editor, entry, start_button, restart_button
    global label3, buttons_indicator, report_indicator, canvas, canvas2, FINAL_TEST

    # Variable to count the number of the written editor rows
    row = 0
    saved_label_row = 0
    try:
        root = create_new_windows(str(TARGET_NAME))
        # Frame sx
        frame_sx = create_frame_base(root, 300, 700, 0, 0, "ne")
        # Frame edit
        frame_editor = create_frame_base(root, 300, 700, 0, 1, "nsew")

        if FINAL_TEST == "true":
            # Input
            entry = create_input(frame_sx, "Seriale parlante", row, 0, row, 1)
            # Inc row index
            row += 1

            # Hardware version row
            create_fixed_output(frame_sx, "Hardware versione", row, 0)
            create_fixed_output(frame_sx, str(HW_VERSION), row, 1)
            # Inc row index
            row += 1

        create_fixed_output(frame_sx, "Pulsanti da controllare ↓", row, 0)
        # Inc row index
        row += 1

        # Saved labels row
        saved_label_row = row

        for z in range(10):
            create_fixed_output(frame_sx, symbols[z], row, 0)
            create_fixed_output(frame_sx, symbols[z+10], row, 1)
            # Inc row index
            row += 1

        # Indicators
        canvas = create_report(frame_sx, "Collaudo pulsanti", row, 0, frame_sx, 100, 100, row, 1)
        buttons_indicator = canvas.create_oval(20, 20, 80, 80, fill="grey")
        # Inc row index
        row += 1
        if FINAL_TEST == "true":
            canvas2 = create_report(frame_sx, "LOG Report", row, 0, frame_sx, 100, 100, row, 1)
            report_indicator = canvas2.create_oval(20, 20, 80, 80, fill="grey")
            # Inc row index
            row += 1

        # Frame button
        frame_buttons = create_frame_base(frame_sx, 400, 200, row, 0, "")
        # Buttons
        start_button = create_new_button(frame_buttons, "Inizio collaudo", 12, 3, start_operation, 300, 10)
        restart_button = create_new_button(frame_buttons, "Nuovo collaudo", 12, 3, restart, 300, 100)

        # Editor
        editor = create_custom_editor(frame_editor, TARGET_NAME, SW_TESTING_VERSION, str(SETT_FILE_VER))

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante create_gui(): {e}\n\n", "red")


def main() -> None:
    """
    @description: Entry point of the testing application. It loads configuration data, initializes the GUI, sets up
                  button labels, and starts the main event loop. If the configuration file is invalid or missing, it
                  outputs a failure message in the editor.
    """
    global labels, frame_sx, saved_label_row, root, status_ok, editor

    try:
        # Import data from file and check input values
        status_ok = import_data_file(toml_file_path)

        if status_ok:
            # Create a new GUI
            create_gui()

            # Editing buttons label values
            labels = []
            for i in range(20):
                # Determines the column (0 for first 10, 1 for the rest)
                label_col = i // 10
                label_row = saved_label_row + (i % 10)
                label = tk.Label(frame_sx, text="", font=("Arial", 16, "bold"), width=20)
                label.grid(row=label_row, column=label_col, padx=1, pady=1)
                labels.append(label)

            # Initial update of labels with a list of zeros
            update_labels([0] * 20)
            set_labels_name()

            root.mainloop()
        else:
            editor.insert(tk.END, "❌ Fine - Collaudo NON SUPERATO!\n", "red")
    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante main(): {e}\n\n", "red")
        editor.insert(tk.END, "❌ Fine - Collaudo NON SUPERATO!\n", "red")


def get_application_path():
    """
    @description: Returns the path to the executable or script folder.
    """
    if getattr(sys, 'frozen', False):
        # Se l'applicazione è un eseguibile creato da PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Se è uno script .py
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path


def import_data_file(file_path) -> bool:
    """
    @description: Loads device and test configuration data from a TOML file and populates global settings.
                  Performs input validation after extraction.

    @param file_path: Path to the TOML configuration file.

    @return result: True if data have been imported correctly, False otherwise
    """
    global PRODUCER, PROD_BATCH, TARGET_NAME, HW_VERSION
    global ANT_ID, RSSI_MIN, SCAN_TIMEOUT, BLE_TIMEOUT, TEST_TIME, MANUFACTURER, SETT_FILE_VER, FINAL_TEST
    global settings, editor

    result = True
    producer_found = False
    manufacturer_found = False

    try:
        # TOML file complete path
        config_path = os.path.join(get_application_path(), file_path)

        # Load the TOML file
        with open(config_path, "rb") as file:
            settings = tomli.load(file)

        # Search producer in producers dictionary
        for producer in producers:
            if producer["name"] == str(settings['BOARD']['producer']).capitalize():
                PRODUCER = producer["internal_code"]
                producer_found = True

        # Search manufacturer in producers dictionary
        for manufacturer in manufacturers:
            if manufacturer["name"] == str(settings['DEVICE']['manufacturer']).capitalize():
                MANUFACTURER = str(settings['DEVICE']['manufacturer']).capitalize()
                manufacturer_found = True

        if not producer_found:
            editor.insert(tk.END, f"❌ PRODUCER non inserito nella lista!\n", "red")
            result = False
        elif not manufacturer_found:
            editor.insert(tk.END, f"❌ MANUFACTURER non inserito nella lista!\n", "red")
            result = False
        else:
            PROD_BATCH = settings['BOARD']['batch']
            TARGET_NAME = str(settings['DEVICE']['type']).upper()
            HW_VERSION = settings['DEVICE']['hw_version']
            ANT_ID = settings['VARIABLES']['ant_id_cnt']
            RSSI_MIN = settings['VARIABLES']['rssi_ths']
            SCAN_TIMEOUT = settings['VARIABLES']['scan_time']
            BLE_TIMEOUT = settings['VARIABLES']['ble_time']
            TEST_TIME = settings['VARIABLES']['time_to_press_buttons']
            SETT_FILE_VER = settings['VARIABLES']['file_ver']
            FINAL_TEST = str(settings['VARIABLES']['final_test']).lower()

            # Check input values
            if not check_input():
                result = False

        return result

    except Exception as e:
        editor.insert(tk.END, f"❌ Errore durante import_data_file(): {e}\n\n")
        return False


def check_input() -> bool:
    """
    @description: Validates configuration values loaded from the TOML file, including board and device parameters.
                  Prints specific error messages to the editor and updates global status if any values are invalid.
    @return result: True if imported data are right, False otherwise
    """
    global PRODUCER, PROD_BATCH, HW_VERSION, ANT_ID
    global editor

    result = True

    try:
        if not 0 <= PRODUCER <= 254:
            # Print to text editor
            editor.insert(tk.END, f"❌ Valore di PRODUCER inserito non valido!\n", "red")
            result = False
        if not 0 <= PROD_BATCH <= 254:
            # Print to text editor
            editor.insert(tk.END, f"❌ Valore di BATCH inserito non valido!\n", "red")
            result = False
        if not 0 <= HW_VERSION <= 254:
            # Print to text editor
            editor.insert(tk.END, f"❌ Valore di HW_VERSION inserito non valido!\n", "red")
            result = False
        if not 1 <= ANT_ID <= 65534 and FINAL_TEST == "true":
            # Print to text editor
            editor.insert(tk.END, f"❌ Valore di ANT_ID inserito non valido!\n", "red")
            result = False

        return result

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante check_input(): {e}\n\n", "red")
        return False


def get_month_code() -> list:
    """
    @description: Generates a code representing the current month and year, using a custom letter mapping for months and
                  a 2-digit suffix for the year.

    @return date: A list containing the letter corresponding to the current month and the last two digits of the
                  current year.
    """
    # List of letters corresponding to the months (A = January, B = February, etc.)
    month_letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", 
                     "U", "V", "W", "X", "Y", "Z"]

    try:
        # Get the current date
        now = datetime.now()

        # Get the current month
        current_month = month_letters[now.month - 1]

        # Get the last two digits of the year
        current_year = str(now.year)[-2:]

        # Return a list with the letter corresponding to the current month and year suffix
        date = [current_month, current_year]
        return date

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante get_month_code(): {e}\n\n", "red")


def number_to_2_bytes(num) -> bytearray | None:
    """
    @description: Converts an integer value into a 2-byte little-endian bytearray. If the input is out of bounds, it
                  prints an error message to the GUI editor.

    @param num: The integer value to convert (must be between 0 and 65535).

    @return bytearray: A 2-byte bytearray representation of the input number, or None if the value is out of range.
    """
    global editor

    try:
        # Ensure the number is between 0 and 65535
        if not (0 <= num <= 65535):
            # Print to text editor
            editor.insert(tk.END, "Il valore deve essere compreso tra 0 e 65535\n\n")
            return

        # Convert the number to 2 bytes (little-endian)
        byte_array = num.to_bytes(2, byteorder='little')

        return byte_array

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante number_to_2_bytes(): {e}\n\n", "red")


def update_labels(array) -> None:
    """
    @description: Updates the color of each button label in the GUI based on its status value. Labels are colored green
                  if active (value > 0), red if inactive.

    @param array: A list of 20 integer values representing button states. Each element controls the foreground color of
                  its corresponding label.
    """
    global labels

    try:
        for j in range(20):
            if array[j] > 0:
                labels[j].config(fg="green")
            else:
                labels[j].config(fg="red")

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante update_labels(): {e}\n\n", "red")


def set_labels_name() -> None:
    """
    @description: Assigns text and color styling to each button label in the GUI. Labels are updated with their
                  corresponding symbol names and set to red color by default.
    """
    global labels

    try:
        for k in range(20):
            labels[k].config(text=symbols[k], fg="red")

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante set_labels_name(): {e}\n\n", "red")


def notification_handler(sender, data) -> None:
    """
    @description: Handles incoming BLE notifications by decoding 4-bit button states, comparing them with previous
                  readings, updating global press tracking, and triggering an event if all required buttons are detected
                  as pressed. Also manages exit/reset behavior for repeated test sessions.

    @param sender: The BLE device or service that sent the notification.
    @param data: A bytearray containing button status encoded in 4-bit values.
    """
    global count_buttons_memory, button_pressed, out_button_pressed, iteration, editor, flag_exit

    print(f"Received data from {sender}: {data}")
    print(f"Notification from {sender}: {data}")

    # Initialize an empty list to store the split 4-bit values
    count_buttons = []

    try:
        # Reset of variables if an exit request from thread is appeared
        if flag_exit:
            flag_exit = False
            count_buttons_memory = [0] * 22
            button_pressed = [0] * 22
            out_button_pressed = [0] * 20
            iteration = 0

        # Loop through each byte in the bytearray
        for byte in data:
            # Extract the higher 4 bits by right-shifting by 4 and store in the list
            high_nibble = ((byte >> 4) & 0x0F)
            count_buttons.append(high_nibble)

            # Extract the lower 4 bits by ANDing with 0x0F and store in the list
            low_nibble = (byte & 0x0F)
            count_buttons.append(low_nibble)

        # Output the result list
        if iteration > 0:
            result = [abs(a - b) for a, b in zip(count_buttons, count_buttons_memory)]
            button_pressed = [x + y for x, y in zip(button_pressed, result)]

            # Format the array
            for a in range(len(button_pressed)):
                if button_pressed[a] > 1:
                    button_pressed[a] = 1

            out_button_pressed = button_pressed[2:]
            update_labels(out_button_pressed)

            # Check if all buttons are pressed
            if all(element == 1 for element in out_button_pressed):
                # Flag to request the exit from thread
                flag_exit = True
                # Signal that all buttons are pressed
                button_event.set()

        iteration += 1
        count_buttons_memory = count_buttons.copy()

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante notification_handler(): {e}\n\n", "red")


def notification_eeprom(sender, data) -> None:
    """
    @description: Handles incoming BLE notifications related to EEPROM operations. Prints the raw data received along
                  with the sender's identifier for debugging purposes.

    @param sender: The BLE device or service that transmitted the EEPROM data.
    @param data: A bytearray containing the EEPROM payload received.
    """
    try:
        print(f"Dati ricevuti da {sender}: {data}\n")

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante notificatin_eeprom(): {e}\n\n", "red")


def check_presence_serial(serial_number, log_file=log_file_path) -> bool:
    """
    @description: Checks whether a given serial number is already present in the specified log file. Iterates through
                  the file entries and compares serial number values to prevent duplicates.

    @param serial_number: The serial number to verify.
    @param log_file: Path to the log file that contains historical serial numbers.

    @return bool: True if the serial number is not found (i.e., it's new), False if already present.
    """
    global editor

    try:
        # Open LOG file to check all SerialNumber values
        with open(log_file, 'r', encoding="utf-8") as data_file:
            rows = data_file.readlines()

        # List of SerialNumber in LOF file
        sn_column = []

        # Extract the SerialNumber value from each LOG file row
        for p in rows[1:]:
            columns = p.strip().split(";")
            if len(columns) >= 3:
                # SerialNumber column has index 2
                sn_column.append(columns[2])

        # Scroll all values in LOG
        for value in sn_column:
            if value == serial_number:
                # Exit to function
                return False

        # SerialNumber is new value
        return True

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante check_presence_serial(): {e}\n\n", "red")
        return False


def is_valid_serial(serial: str) -> bool:
    """
    @description: Validates the format and content of a given serial number string. It checks the prefix, date encoding,
                  progressive counter, crc fields. Prints validation feedback to the GUI editor and returns the result.

    @param serial: The serial number string to validate.

    @return result: True if the serial number is valid according to the specified rules, False otherwise.
    """
    global editor, elite_devices, TARGET_NAME

    try:
        result = True
        dev_found = False
        serial_num_code = ""
        serial_num_length = 0

        # List for date
        date = get_month_code()

        # Extraction of SerialNumber fields
        mounth = str(serial[2])
        year = int(serial[3:5])
        counter = int(serial[5:9])
        crc = int(serial[9:13], 16)
        input_data = serial[0:9]
        calculated_crc = crc16_from_str(input_data)

        # Search desired device in elite devices dictionary
        for device in elite_devices:
            if device["name"].upper() == TARGET_NAME:
                # Extract value of desired device
                serial_num_code = str(device["sn_code"]).upper()
                serial_num_length = int(device["sn_length"])
                dev_found = True

        if not dev_found:
            editor.insert(tk.END, f"⚠️ Dispositivo non trovato\n\n", "red")
            result = False
        else:
            if not serial[:2] == serial_num_code:
                # Print to text editor
                editor.insert(tk.END, f"⚠️ Codice dispositivo riportato nel seriale non valido\n\n", "red")
                result = False
            if not len(serial) == serial_num_length:
                # Print to text editor
                editor.insert(tk.END, f"⚠️ Lunghezza del seriale non valida\n\n", "red")
                result = False
            if (not "A" <= mounth <= "L") or (mounth != date[0]):
                # Print to text editor
                editor.insert(tk.END, f"⚠️ ATTENZIONE: Mese inserito non attuale\n\n", "orange")
            if (not 0 <= year <= 99) or (str(year) != date[1]):
                # Print to text editor
                editor.insert(tk.END, "⚠️ ATTENZIONE: Anno inserito non attuale\n\n", "orange")
            if not 0 <= counter <= 9999:
                # Print to text editor
                editor.insert(tk.END, "⚠️ Progressivo inserito non valido\n\n", "red")
                result = False
            if not calculated_crc == crc:
                # Print to text editor
                editor.insert(tk.END, "⚠️ CRC inserito non valido\n\n", "red")
                result = False
        return result

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante is_valid_serial(): {e}\n\n", "red")
        return False


def increase_ant_id(value) -> None:
    """
    @description: Validates and increments the ANT ID counter stored in the configuration file. Resets the value to 1
                  if it reaches the upper limit. Updates the TOML file and prints the result or any error message to
                  the GUI editor.

    @param value: The current ANT ID counter to validate and increment.
    """
    global editor

    try:
        # Validation
        if not (1 <= value <= 65534):
            # Print to text editor
            editor.insert(tk.END, f"❌ ANT ID caricato dal file {toml_file_path} non valido!!\n\n", "red")
            return

        # Increase o reset
        value = 1 if value == 65534 else value + 1

        # Assign new ANT ID value
        settings["VARIABLES"]["ant_id_cnt"] = value

        # TOML file complete path
        config_path = os.path.join(get_application_path(), toml_file_path)

        # Write new ANT ID value in toml file
        with open(config_path, "wb") as sett_file:
            tomli_w.dump(settings, sett_file)

        # Print to text editor
        editor.insert(tk.END, f"ANT ID aggiornato: {value}\n\n")
    except FileNotFoundError:
        print("File di configurazione mancante.")
    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante increase_ant_id: {e}", "red")


def write_log(query_fields, filename=log_file_path) -> None:
    """
    @description: Writes header information to a log file. If the file does not exist or is empty, it creates the file
                  and inserts the formatted header line using semicolon-separated fields.

    @param query_fields: A list of strings representing column names to be written as the header.
    @param filename: Path to the log file where the header should be written.
    """
    try:
        # Check if the file exists and has content
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            # If file is new or empty, write the header
            with open(filename, 'w') as data_file:
                data_file.write(';'.join(query_fields) + '\n')

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante write_log(): {e}\n\n", "red")


def write_report_log(ble_address, serial_number, fw_version, ant_id, result) -> None:
    """
    @description: Generates and appends a formatted report entry to the log file, including metadata about the
                  BLE device, test execution details, and serial identification. The log header is written if missing
                  or empty.

    @param ble_address: The BLE address of the tested device.
    @param serial_number: The serial number used for identification.
    @param fw_version: The firmware version of the device.
    @param ant_id: The ANT identifier associated with the test unit.
    @param result: The result of test ("OK" = pass, "ERR" = fail).
    """
    global editor

    try:
        # Create the query dictionary using query_fields
        query: dict[str, str | int | None] = {}

        # Define the query fields
        query_fields = ['Date', 'Time', 'Serial_Number', 'ANT_ID', 'FWVersion', 'HWVersion', 'SW_Testing', 'Batch',
                        'Producer', 'Manufacturer', 'BLE_Addr', 'Result']

        # Call the function to write to the log file (only if new or empty)
        write_log(query_fields, log_file_path)

        # Prepare the list of data to write in LOG file
        query['Date'] = datetime.now().strftime("%d/%m/%Y")
        query['Time'] = datetime.now().strftime("%H:%M")
        query['Serial_Number'] = serial_number
        query['ANT_ID'] = ant_id
        query['FWVersion'] = fw_version
        query['HWVersion'] = HW_VERSION
        query['SW_Testing'] = SW_TESTING_VERSION
        query['Batch'] = PROD_BATCH
        query['Producer'] = PRODUCER
        query['Manufacturer'] = MANUFACTURER
        query['BLE_Addr'] = ble_address
        query['Result'] = result

        # Open the file in append mode
        with open(log_file_path, 'a') as log_data_file:
            # Write all values in a single line, separated by a space
            log_data_file.write(';'.join(str(value) for value in query.values()) + '\n')

        # Print to text editor
        editor.insert(tk.END, "Il report di LOG è stato generato\n\n")
        set_indicator(canvas2, report_indicator, "green")
    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante write_report_log(): {e}", "red")
        set_indicator(canvas2, report_indicator, "red")


def set_indicator(canv: tk.Canvas, indicator: int, colour: str) -> None:
    """
    @description: Updates the fill color of the buttons indicator displayed in the GUI. Only accepted colors defined in
                  ValidColours are allowed. If an invalid color is passed or an update error occurs, the issue is logged
                  in the text editor.
    @param canv:
    @param indicator:
    @param colour: Name of the color to apply to the buttons indicator element.
    """
    global editor

    if colour not in ValidColours:
        print(f"Colore non valido: '{colour}'")
        return

    try:
        canv.itemconfig(indicator, fill=colour)
    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante set_indicator(): {e}\n\n", "red")


def start_operation() -> None:
    """
    @description: Initiates the button testing workflow and prepares the GUI for execution. Displays a log message,
                  resets visual indicators, and validates the serial number if required. The actual test process runs
                  asynchronously in a separate thread.
    """
    global editor, start_button, first_test, user_input, status_ok, FINAL_TEST

    try:
        # Print to text editor
        editor.insert(tk.END, "INIZIO COLLAUDO\n\n", "bold")

        # Reset button and indicatore state
        start_button.config(state=tk.DISABLED)
        restart_button.config(state=tk.ACTIVE)
        if FINAL_TEST == "true":
            set_indicator(canvas2, report_indicator, "grey")
        set_indicator(canvas, buttons_indicator, "grey")

        # Insert and check SerialNumber only if there is the first test
        if first_test and FINAL_TEST == "true":
            user_input = insert_serial_number()
            if check_serial_number(user_input):
                # Print to text editor
                editor.insert(tk.END, "✅ Seriale inserito valido\n\n")
            else:
                status_ok = False

        # Run the async operation in a separate thread to avoid blocking the main thread
        threading.Thread(target=run_async_operation).start()
    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante start_operation(): {e}\n\n", "red")


def restart() -> None:
    """
    @description: Resets the GUI and internal variables to prepare for a new button testing session.
                  Clears input fields, restores label layout, resets indicators, and reinitializes status values.
    """
    global editor, entry, user_input, start_button, labels, saved_label_row, status_ok, first_test
    global out_button_pressed, button_pressed, count_buttons_memory, iteration

    try:
        # Reset editor
        editor.delete("1.0", tk.END)
        # Reset fields
        if FINAL_TEST == "true":
            entry.delete(0, tk.END)

        # Reset variables
        status_ok = True
        start_button.config(state=tk.ACTIVE)
        set_indicator(canvas, buttons_indicator, "grey")
        if FINAL_TEST == "true":
            set_indicator(canvas2, report_indicator, "grey")

        # Editing buttons label values
        labels = []
        for i in range(20):
            # Determines the column (0 for first 10, 1 for the rest)
            label_col = i // 10
            label_row = saved_label_row + (i % 10)
            label = tk.Label(frame_sx, text="", font=("Arial", 16, "bold"), width=20)
            label.grid(row=label_row, column=label_col, padx=1, pady=1)
            labels.append(label)
        
        # Initial update of labels with a list of zeros
        update_labels([0] * 20)
        set_labels_name()

        # Initial text
        editor.insert(tk.END, f"SOFTWARE DI COLLAUDO - {TARGET_NAME}\n", "bold_yellow")
        editor.insert(tk.END, f"SW version: {SW_TESTING_VERSION}\n", "yellow")
        editor.insert(tk.END, f"File version: {SETT_FILE_VER}\n\n", "yellow")

        # After first button press, reset the flag
        if first_test:
            first_test = False

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante restart(): {e}\n\n", "rosso")


def run_async_operation() -> None:
    """
    @description: Initializes and runs a new asyncio event loop to execute the main asynchronous testing operation in a
                  non-blocking context. This allows BLE communication and testing tasks to operate independently of
                  the GUI thread.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_operation())

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante run_async_operation(): {e}\n\n", "red")


async def scan_get_sorted_devices(desired_type: str) -> list:
    """
    @description: Scans for nearby BLE devices and filters the results based on a desired device name and RSSI
                  threshold. Returns a list of matching devices sorted by signal strength, or displays a warning
                  if none are found.

    @param desired_type: The name of the BLE device type to search for.

    @return sorted_devices: A list of tuples containing matching BLE devices data, sorted by RSSI.
    """
    global editor

    # Scan for BLE devices
    devices = await BleakScanner.discover(timeout=SCAN_TIMEOUT, return_adv=True)

    if not devices:
        # Print to text editor
        editor.insert(tk.END, "⚠️Nessun dispositivo BLE trovato\n")
        return []

    try:
        # Create a new dict where insert only square devices
        square_devices = {
            address: (device, adv)
            for address, (device, adv) in devices.items()
            if (device.name == desired_type) or (adv.local_name == desired_type) and
               (adv.rssi is not None and adv.rssi >= RSSI_MIN)
        }

        # Sort devices by RSSI (signal strength)
        sorted_devices = sorted(square_devices.items(), key=lambda x: x[1][1].rssi, reverse=True)

        # Return the sorted list of devices
        return sorted_devices

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌Errore durante scan_get_sorted_devices(): {e}\n", "red")


def insert_serial_number() -> str:
    """
    @description: Retrieves the serial number input from the GUI entry field and returns it as a string. This value is
                  used to validate and track the current test session.

    @return input_ser_value: The serial number entered by the user.
    """
    try:
        # Insert SerialNumber
        input_ser_value = entry.get()

        return input_ser_value.upper()

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante insert_serial_number(): {e}\n\n", "red")


def check_serial_number(input_value) -> bool:
    """
    @description: Validates the given serial number by format and duplication. First, it checks if the serial is
                  structurally correct. Then it verifies whether the serial number is already present in the log file.
                  If duplicate, a warning is printed to the GUI editor.

    @param input_value: The serial number string to validate and verify for uniqueness.

    @return status: True if the serial number is valid and not previously recorded, False otherwise.
    """
    status = True

    try:
        # Check serial number
        if not is_valid_serial(input_value):
            status = False
        else:
            # Check if SerialNumber has already written in LOG file
            if not check_presence_serial(input_value, log_file_path):
                # Print to text editor
                editor.insert(tk.END, f"⚠️ ATTENZIONE: Serial Number {input_value} gia' registrato!\n\n", "orange")

        return status

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante check_serial_number(): {e}\n\n", "red")
        return False


async def async_operation() -> None:
    """
    @description: Executes the full BLE-based functional test routine asynchronously. Scans for nearby Square devices,
                  connects to the selected device, verifies hardware interactions, performs EEPROM programming (if
                  enabled), and handles GUI feedback and reporting accordingly. Manages timeout, validation, and user
                  prompts while ensuring proper session finalization.
    """
    global editor, out_button_pressed, status_ok, user_input, first_test, flag_exit
    global PROD_BATCH, PRODUCER, FINAL_TEST, HW_VERSION, ANT_ID
    ble_address = ""
    name = ""

    try:
        # Reset old values if an exit from thread is appeared
        if flag_exit:
            out_button_pressed = [0] * 20

        if not first_test:
            # Import data from settings file and check input values
            status_ok = import_data_file(toml_file_path)
            if status_ok:
                if FINAL_TEST == "true":
                    # Insert and check SerialNumber
                    user_input = insert_serial_number()
                    if check_serial_number(user_input):
                        # Print to text editor
                        editor.insert(tk.END, "✅ Seriale inserito valido\n\n")
                    else:
                        status_ok = False

        if status_ok:
            # Print to text editor
            editor.insert(tk.END, "🔍 Scansione dispositivi BLE in corso. Attendere...\n\n")

            # Find Square devices near
            all_squares_devices = await scan_get_sorted_devices(TARGET_NAME)
            if not all_squares_devices:
                # Print to text editor
                editor.insert(tk.END,
                              f"⚠️ Nessun dispositivo {TARGET_NAME} trovato con RSSI ≥ {RSSI_MIN} dBm.\n", "red")
                status_ok = False
            else:
                # Select SQUARE device nearer
                ble_address, (target_device, target_adv) = all_squares_devices[0]
                name = target_device.name or target_adv.local_name or TARGET_NAME

        if status_ok:
            # Print to text editor
            editor.insert(tk.END, f"📶 Dispositivo {name} trovato! Add:{ble_address}\n")
            editor.insert(tk.END, "Attendere connessione col dispositivo...\n\n")

            try:
                async with BleakClient(ble_address, timeout=BLE_TIMEOUT) as client:
                    # Reset event and flag before starting
                    button_event.clear()

                    # Ensure that the client is connected
                    if client.is_connected:
                        # Check buttons
                        await client.start_notify(SQUARE_BUTTONS_CHAR, notification_handler)
                        # Print to text editor
                        editor.insert(tk.END, "🔗 Connesso! Puoi iniziare il collaudo funzionale\n\n")
                        time.sleep(1)
                        editor.insert(tk.END, f"Premere tutti i pulsanti entro {TEST_TIME}s\n")
                        time.sleep(0.5)
                        editor.insert(tk.END, "NON DIMENTICARE DI TESTARE I LED!\n", "bold")
                        time.sleep(0.5)
                        editor.insert(tk.END, "NON DIMENTICARE DI TESTARE I FRENI!\n\n", "bold")

                        try:
                            # Wait for event with timeout
                            await asyncio.get_event_loop().run_in_executor(None,
                                                                           lambda: button_event.wait(timeout=TEST_TIME))
                        except asyncio.TimeoutError:
                            # Print to text editor
                            editor.insert(tk.END, "❌ Timeout scaduto!\n\n", "red")
                            status_ok = False

                        # Stop notifications/indications
                        await client.stop_notify(SQUARE_BUTTONS_CHAR)

                        if all(element == 1 for element in out_button_pressed) and status_ok:
                            # Print to text editor
                            editor.insert(tk.END, "Tutti i pulsanti sono stati premuti\n\n")
                            set_indicator(canvas, buttons_indicator, "green")

                            # Notifications/indications enabled
                            await client.start_notify(UUID_EEPROM_RESULT, notification_eeprom)

                            # Read SW version from BLE
                            sw_version = await client.read_gatt_char("2A28")
                            fw_version = sw_version.decode('utf-8')
                            # Read ANT ID from BLE
                            ant_id_from_char = await client.read_gatt_char("2A25")
                            print(f"Valore di ANT ID letto da BLE: {int(ant_id_from_char)}\n")

                            # Manufacturer test
                            if FINAL_TEST == "true":
                                # Read production batch loaded from EEPROM
                                PROD_BATCH = await read_eeprom_parameter(client, EEPROM_BATCH_READ_REQUEST)
                                # Read producer loaded from EEPROM
                                PRODUCER = await read_eeprom_parameter(client, EEPROM_PRODUCER_READ_REQUEST)
                                # Write HW version loaded from toml
                                await write_eeprom_parameter(client, 1, EEPROM_HWVER_WRITE_REQUEST, HW_VERSION)
                                # Write ANT ID loaded from toml
                                await write_eeprom_parameter(client, 2, EEPROM_ANTID_WRITE_REQUEST, ANT_ID)
                                time.sleep(1)
                                # Read written HW_VERSION from EEPROM
                                tmp_hw = await read_eeprom_parameter(client, EEPROM_HWVER_READ_REQUEST)
                                # Read written ANT_ID from EEPROM
                                tmp_aid = await read_eeprom_parameter(client, EEPROM_ANTID_READ_REQUEST)

                                # Print to text editor
                                editor.insert(tk.END, f"Dati scritti in EEPROM\n", "bold")
                                editor.insert(tk.END, f"HW Version: {HW_VERSION}\n")
                                editor.insert(tk.END, f"ANT-ID: {ANT_ID}\n\n")

                                # Print to text editor
                                editor.insert(tk.END, f"Dati letti da EEPROM\n", "bold")
                                editor.insert(tk.END, f"Produttore: {PRODUCER}\n")
                                editor.insert(tk.END, f"Lotto: {PROD_BATCH}\n\n")

                                if tmp_hw != HW_VERSION or tmp_aid != ANT_ID:
                                    editor.insert(tk.END, "❌ Scrittura in EEPROM non valida!\n\n", "red")
                                    status_ok = False
                                else:
                                    editor.insert(tk.END, f"Dati scritti in EEPROM letti correttamente\n\n")

                            # Producer test
                            else:
                                # Write batch (numero lotto) number loaded from toml
                                await write_eeprom_parameter(client, 1, EEPROM_BATCH_WRITE_REQUEST, PROD_BATCH)
                                # Write producer number loaded from toml
                                await write_eeprom_parameter(client, 1, EEPROM_PRODUCER_WRITE_REQUEST, PRODUCER)
                                time.sleep(1)
                                # Read written HW_VERSION from EEPROM
                                tmp_bat = await read_eeprom_parameter(client, EEPROM_BATCH_READ_REQUEST)
                                # Read written ANT_ID from EEPROM
                                tmp_prod = await read_eeprom_parameter(client, EEPROM_PRODUCER_READ_REQUEST)

                                # Print to text editor
                                editor.insert(tk.END, f"Dati scritti in EEPROM\n", "bold")
                                editor.insert(tk.END, f"Produttore: {PRODUCER}\n")
                                editor.insert(tk.END, f"Lotto: {PROD_BATCH}\n\n")

                                if tmp_bat != PROD_BATCH or tmp_prod != PRODUCER:
                                    editor.insert(tk.END, "❌ Scrittura in EEPROM non valida!\n\n", "red")
                                    status_ok = False
                                else:
                                    editor.insert(tk.END, f"Dati scritti in EEPROM letti correttamente\n\n")

                            # Notifications/indications disabled
                            await client.stop_notify(UUID_EEPROM_RESULT)

                            # Print to text editor
                            editor.insert(tk.END, "Spegnimento Square...\n\n")
                            # 0x01 shout down, 0x00 sleep
                            await client.write_gatt_char(SQUARE_CONTROL_POINT, bytearray([0x0A, 0x00]), response=False)
                        else:
                            # Print to text editor
                            editor.insert(tk.END, "❌ Fallimento: pulsanti non funzionano!\n", "red")
                            # set_indicator(canvas, buttons_indicator, "red")
                            status_ok = False
                    else:
                        # Print to text editor
                        editor.insert(tk.END, "❌ Connessione BLE persa!\n", "red")
                        # set_indicator(canvas, buttons_indicator, "red")
                        status_ok = False
            except Exception as e:
                # Print to text editor
                editor.insert(tk.END, f"❌ Connessione BLE fallita! {e}\n", "red")
                status_ok = False

        # Exit from thread
        flag_exit = True

        if status_ok:
            if FINAL_TEST == "true":
                # Write report LOG only in final test
                write_report_log(ble_address, user_input, fw_version, ANT_ID, "OK")
                # Prepare ANT ID for next device only in last phase of the process
                increase_ant_id(ANT_ID)
            # Print to text editor
            editor.insert(tk.END, "✅ Fine - Collaudo SUPERATO!\n\n", "green")
        else:
            # Print to text editor and signal on report indicator
            if FINAL_TEST == "true":
                set_indicator(canvas2, report_indicator, "red")
            set_indicator(canvas, buttons_indicator, "red")
            editor.insert(tk.END, "❌ Fine - Collaudo NON SUPERATO!\n\n", "red")
            # Close BLE connection
            await client.disconnect()
            await asyncio.sleep(1 - 2)

    except Exception as e:
        # Print to console
        print(f"❌ Errore durante async_operation(): {e}\n\n")


def create_new_windows(name: str) -> tk.Tk:
    """
    @description: Creates and configures the main application window for the test GUI. Sets title and size, and applies
                  initial grid layout for left and right sections.

    @param name: The base name used in the window title (e.g., device or project identifier).

    @return window: The newly initialized and configured Tkinter window object.
    """
    try:
        # Principle window
        window = tk.Tk()
        window.title(f"{name} testing")
        window.geometry('1620x850')

        # Set custom icon
        icon_path = os.path.join(get_application_path(), "elite.ico")
        if os.path.exists(icon_path):
            window.iconbitmap(icon_path)
        else:
            raise FileNotFoundError(f"⚠️ Icon file not found: {icon_path}\n\n", "orange")

        # Column expansion (SX: fixed, DX: expansion)
        window.grid_columnconfigure(0, weight=0)
        window.grid_columnconfigure(1, weight=1)
        window.grid_rowconfigure(0, weight=1)

        return window

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante create_windows(): {e}\n\n", "red")


def create_frame_base(widget, width: int, height: int, row: int, column: int, sticky: str) -> tk.Frame:
    """
    @description: Creates and places a Tkinter frame within a parent window or container. The frame has fixed width and
                  height, and is placed using grid layout with custom row, column, alignment, and padding configuration.

    @param widget: The parent Tkinter widget in which the frame will be placed.
    @param width: The width of the frame in pixels.
    @param height: The height of the frame in pixels.
    @param row: The row index in the grid where the frame will be placed.
    @param column: The column index in the grid where the frame will be placed.
    @param sticky: The sticky alignment value (e.g. "n", "se", "nsew").

    @return frame: The configured frame widget.
    """
    try:
        frame = tk.Frame(widget, width=width, height=height)
        frame.grid(row=row, column=column, sticky=sticky, padx=10, pady=10)

        return frame

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante create_frame_base(): {e}\n\n", "red")


def create_input(frame, testo: str, row1: int, column1: int, row2: int, column2: int) -> tk.Entry:
    """
    @description: Creates a labeled input field within the specified Tkinter frame. A label is displayed above the entry
                  box, both placed using grid layout.

    @param frame: The parent Tkinter frame where the label and entry are placed.
    @param testo: The text to display as the label above the entry box.
    @param row1: Grid row index for the label.
    @param column1: Grid column index for the label.
    @param row2: Grid row index for the entry field.
    @param column2: Grid column index for the entry field.

    @return e: The configured entry widget for user input.
    """
    try:
        # Create a label
        l_input = tk.Label(frame, text=testo, font=("Arial", 12))
        l_input.grid(row=row1, column=column1, sticky="ew", padx=1, pady=5)
        # Create a bow where the value can be insered
        e = tk.Entry(frame, width=16)
        e.grid(row=row2, column=column2, sticky="ew", padx=5)
        e.focus_set()

        return e

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante create_input(): {e}\n\n", "red")


def create_fixed_output(frame, text: str, row: int, column: int) -> None:
    """
    @description: Creates a static output label within a specified Tkinter frame. The label is positioned using grid
                  layout with padding and alignment.

    @param frame: The parent Tkinter frame in which the label will be placed.
    @param text: The text content to display in the label.
    @param row: Grid row index for placing the label.
    @param column: Grid column index for placing the label.
    """
    try:
        tk.Label(frame, text=text, font=("Arial", 12)).grid(row=row, column=column, sticky="ew", padx=10, pady=5)

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante create_fixed_output(): {e}\n\n", "red")


def create_report(f1: tk.Frame, t: str, r1: int, c1: int, f2: tk.Frame, w: int, h: int, r2: int, c2: int) -> tk.Canvas:
    """
    @description: Creates a labeled section composed of a text label and a canvas element in two separate frames. The
                  label provides context or a title, while the canvas can be used as a graphical indicator or for
                  drawing content.

    @param f1: The Tkinter frame where the label will be placed.
    @param t: The text content for the label.
    @param r1: Grid row index for placing the label.
    @param c1: Grid column index for placing the label.
    @param f2: The Tkinter frame where the canvas will be placed.
    @param w: Width of the canvas in pixels.
    @param h: Height of the canvas in pixels.
    @param r2: Grid row index for placing the canvas.
    @param c2: Grid column index for placing the canvas.

    @return canv: The created canvas widget, ready for drawing or styling.
    """
    try:
        lab = tk.Label(f1, text=t, font=("Arial", 12))
        lab.grid(row=r1, column=c1, padx=1, pady=1)
        canv = tk.Canvas(f2, width=w, height=h)
        canv.grid(row=r2, column=c2, padx=1, pady=1)

        return canv

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante create_report(): {e}\n\n", "red")


def create_new_button(frame, text: str, width: int, height: int, command, x: int, y: int) -> tk.Button:
    """
    @description: Creates and places a Tkinter button within a given frame using absolute positioning. The button is
                  configured with the provided text, dimensions, and command callback.

    @param frame: The parent Tkinter frame or container where the button will be placed.
    @param text: The text to be displayed on the button.
    @param width: The width of the button.
    @param height: The height of the button.
    @param command: The function to be called when the button is clicked.
    @param x: The horizontal (x-axis) coordinate for placing the button.
    @param y: The vertical (y-axis) coordinate for placing the button.

    @return button: The created button widget.
    """
    try:
        button = tk.Button(frame, text=text, width=width, height=height, command=command)
        button.place(x=x, y=y)

        return button

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante create_new_button(): {e}\n\n", "red")


def create_custom_editor(frame, device_name, sw_test_vers: str, sett_file_vers: str) -> ScrolledText:
    """
    @description: Creates and configures a scrollable text editor widget for displaying test logs and feedback. Applies
                  styling tags for colored output, sets initial header text with software and file version details, and
                  returns the widget.

    @param frame: The Tkinter frame that will contain the scrollable text editor.
    @param device_name: The name of the test device to include in the editor header.
    @param sw_test_vers: The software version string to display.
    @param sett_file_vers: The settings file version string to display.

    @return ScrolledText: The initialized text editor widget with styling and header text.
    """
    try:
        edit = ScrolledText(frame, font=("Consolas", 11), bg="black", fg="white", insertbackground="white")
        edit.pack(fill="both", expand=True)

        # Tags configuration
        edit.tag_configure("green", foreground="green")
        edit.tag_configure("red", foreground="red")
        edit.tag_configure("orange", foreground="orange")
        edit.tag_configure("yellow", foreground="yellow", font=("Consolas", 10))
        edit.tag_configure("bold_yellow", foreground="yellow", font=("Consolas", 14, "bold"))
        edit.tag_configure("bold", font=("Consolas", 12, "bold"))

        # Initial text
        edit.insert(tk.END, f"SOFTWARE DI COLLAUDO - {device_name}\n", "bold_yellow")
        edit.insert(tk.END, f"SW version: {sw_test_vers}\n", "yellow")
        edit.insert(tk.END, f"File version: {sett_file_vers}\n\n", "yellow")

        return edit

    except Exception as e:
        # Print to text editor
        editor.insert(tk.END, f"❌ Errore durante create_custom_editor(): {e}\n\n", "red")


async def read_eeprom_parameter(client: BleakClient, parameter_req) -> int:
    """
    @description: Sends a read request to the BLE device for a specific EEPROM parameter, then reads and decodes
                  the response, extracting the payload and converting it to an integer using little-endian format.

    @param client: Connected BLE client used to communicate with the target device.
    @param parameter_req: Byte sequence representing the EEPROM read request.

    @return data: Integer value decoded from the EEPROM payload.
    """
    try:
        # Write on BLE an EEPROM parameter read request
        await client.write_gatt_char(UUID_EEPROM_WRITE, parameter_req)
        # Read EEPROM parameter data from BLE
        value = await client.read_gatt_char(UUID_EEPROM_READ)

        # Extract data length (2 bytes little endian) to 3 up 4 indexes
        length = int.from_bytes(value[3:5], byteorder='little')

        # Extract payload to index 5
        data_bytes = value[5:5 + length]

        # Decode data (little endian)
        data = int.from_bytes(data_bytes, byteorder='little')

        # Return decoded data
        return data
    except Exception as e:
        editor.insert(tk.END, f"❌ Errore durante read_eeprom_parameter(): {e}\n", "red")


async def write_eeprom_parameter(client: BleakClient, byte_length, parameter_req, value) -> None:
    """
    @description: Writes a parameter value to the BLE device's EEPROM using the specified request code.
                  Handles formatting based on the byte length (1 or 2 bytes), applying big or little endian conversion
                  as required. If an unsupported length is provided, a warning is displayed.

    @param client: Connected BLE client used to communicate with the target device.
    @param byte_length: Number of bytes to encode the value (supported: 1 or 2).
    @param parameter_req: Byte sequence representing the EEPROM request prefix.
    @param value: Integer value to be encoded and written to the EEPROM.
    """
    try:
        # Prepare data to write in right format (little endian, only if data >= 2 bytes)
        if byte_length == 1:
            value_byte = value.to_bytes(byte_length, byteorder='big')
        elif byte_length == 2:
            value_byte = number_to_2_bytes(value)
        else:
            value_byte = 0
            editor.insert(tk.END, f"Lunghezza del dato non gestita\n", "orange")

        # Write data on EEPROM
        await client.write_gatt_char(UUID_EEPROM_WRITE, parameter_req + value_byte)
    except Exception as e:
        editor.insert(tk.END, f"❌ Errore durante write_eeprom_parameter(): {e}\n", "red")


#######################################################################################################################
# PROGRAM
#######################################################################################################################

# Start main program
main()
