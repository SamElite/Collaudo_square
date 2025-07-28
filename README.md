# Square Testing Application

A Python application for testing Square devices with a graphical interface. 

## Features

- Bluetooth LE device scanning and connection
- Button testing interface with visual feedback
- Hardware version verification 
- Serial number validation
- Test result logging
- Configuration via TOML files

## Requirements

- Python >=3.12
- Bluetooth LE capable hardware
- Required Python packages:
  - tkinter
  - asyncio
  - bleak
  - toml

## Configuration

The application uses a TOML configuration files:

### settings.toml
```toml
[BOARD]
producer = "Default"
batch = 0

[DEVICE]
manufacturer = "Default"
type = "Square"
hw_version = 0

[VARIABLES]
ant_id_cnt = 1
rssi_ths = -55
scan_time = 5.0
ble_time = 10.0
time_to_press_buttons = 30
file_ver = 2.0
final_test = "true"
```

### Field Descriptions

1. **BOARD**
   - producer: nome del produttore/collaudatore delle schede, da scrivere in EEPROM
   - batch: numero del lotto di produzione, da scrivere in EEPROM

2. **DEVICE**
   - manufacturer: nome del terzista che assembla/collauda il prodotto finale, da scrivere in EEPROM
   - type: nome del prodotto
   - hw_versione: numero dell'hw_version, da scrivere in EEPROM
  
3. **VARIABLES**
   - ant_id_cnt: numero incrementale che verrà scritto nel seriale ANT del prossimo dispositivo testato 
   - rssi_ths: soglia in dB per determinare i dispositivi vicini
   - scan_time: timeout sul tempo di scansione dei dispositivi BLE
   - ble_time: timeout sul tempo di connessione con il dispositivo BLE selezionato
   - time_to_press_buttons: timeout sul tempo del test dei pulsanti
   - file_ver: versione del file settings.toml
   - final_test: "true" = collaudo del terzista, "false" = collaudo del produttore
   
## Usage

1. Launch the application:
start the launch_testing.bat, or
   ```batch
   python square_test_v1_16.py
   ```

2. Interface Elements:
   - Serial number input field ("Seriale parlante")
   - Hardware version display
   - Start button
   - 20 button status indicators
   - Test report indicator
   - Restart button

3. Testing Process:
   - Enter a valid serial number
   - Click "Start"
   - The system will:
     1. Scan for nearby Square devices
     2. Connect to the closest device
     3. Begin button testing session
   - Press all device buttons within the configured timeout (time expressed in seconds from configuration file)
   - Watch indicators turn green for successful button presses
   - Wait for final report status

## Data Logging

The application logs test results in CSV format to `sap_log.txt`. Each test record is stored as a semicolon-separated line.

### Log Format Examples
```csv
Date;Time;Serial_Number;ANT_ID;FWVersion;HWVersion;SW_Testing;Batch;Producer;Manufacturer;BLE_Addr;Result
24/07/2025;15.28.58;SQF2500000001;20;14;77;1.2;244;1;Brotto;FE:75:56:03:E3:CC;OK
```

### Field Descriptions

1. **Date** (DD/MM/YYYY)
   - Example: `24/07/2025` (July 24, 2025)

2. **Time** (HH.MM.SS)
   - Example: `15.28.58` (15:28:58)

3. **Serial_Number** - Square device serial number
   - Example: `SQF2500000001`

4. **ANT_ID** - ANT serial number   
   - Example: `20`

5. **FWVersion** - Firmware version
   - Format: Integer
   - Example: `14`

6. **HWVersion** - Hardware version
   - Format: Integer
   - Example: `77`

7. **SW_Testing** - Testing software version
   - Current version: `1.2`

8. **Batch** - Production batch number
   - Example: `244`

9. **Producer** - Producer ID number
   - Example: `1`

10. **Manufacturer** - Manufacturing contractor name
    - Example: `Brotto`
   
11. **BLE_Addr** - Bluetooth Low-Energy device address
    - Example: `FE:75:56:03:E3:CC`
   
12. **Result** - Result of test
    - Example: `OK`

### File Location
The log file `sap_log.txt` is automatically created in the application root directory. New test results are appended to the existing file.

### Data Format Rules
- Fields are semicolon-separated (;)
- No spaces between fields
- Date format: DD/MM/YYYY with forward slashes
- Time format: HH.MM.SS with periods
- All fields are mandatory
- Missing values are logged as empty fields (;;)

## Known Issues

1. Performance:
   - Slow device discovery, especially in environments with many BLE devices
   - Slow connection to a BLE device once selected

2. Error Handling:
   - No retry mechanism for failed connections

## Troubleshooting

If you encounter issues:

1. Ensure Bluetooth is enabled on your system
2. Check if the Square device is powered on
3. Verify the serial number format (SQ + 11 characters)
4. Restart the application if connection fails
5. Check the Windows Event Viewer for BLE-related errors

