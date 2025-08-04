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
[manufacturer]
producer = 1
contractor = "Elite" 
time_to_press_buttons = 45
batch = 1

[device]
type = "Square"
counter = 1
hw_version = 1
```

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
   - Enter a valid serial number (a check in the code needs to be added)
   - Click "Start"
   - The system will:
     1. Scan for nearby Square devices
     2. Connect to the closest device
     3. Begin button testing session
   - Press all device buttons within the configured timeout (45 seconds)
   - Watch indicators turn green for successful button presses
   - Wait for final report status

## Data Logging

The application logs test results in CSV format to `sap_log.txt`. Each test record is stored as a semicolon-separated line.

### Log Format Examples
```csv
08/01/2025;14.59.10;SQA250003181B;271;13;1;0.1;1;1;Elite;
08/01/2025;15.02.14;SQA2500044708;21;12;1;0.1;1;1;Elite;
```

### Field Descriptions

1. **Date** (DD/MM/YYYY)
   - Example: `08/01/2025` (January 8, 2025)

2. **Time** (HH.MM.SS)
   - Example: `14.59.10` (14:59:10)

3. **self-expl-ID** - Square device serial number
   - Example: `SQA250003181B`

4. **ANT-SN** - ANT serial number   
   - Example: `271`, `21`

5. **FWVersion** - Firmware version
   - Format: Integer
   - Example: `13`, `12`

6. **HWVersion** - Hardware version
   - Format: Integer
   - Example: `1`

7. **SW_Testing** - Testing software version
   - Current version: `0.1`

8. **Batch** - Production batch number
   - Example: `1`

9. **Producer** - Producer ID number
   - Example: `1`

10. **Contractor** - Manufacturing contractor name
    - Example: `Elite`

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

1. Testing Process:
   - Button test continues until timeout even if all buttons are pressed
   - Command window remains open after GUI closure
   - "UUID already registered" warning always appears on connection

2. Input Validation:
   - Serial number validation/check needs to be added
   - No input sanitization for special characters

3. Performance:
   - Slow device discovery, especially in environments with many BLE devices

4. Error Handling:
   - Limited error messages for BLE connection failures
   - No retry mechanism for failed connections

## Troubleshooting

If you encounter issues:

1. Ensure Bluetooth is enabled on your system
2. Check if the Square device is powered on
3. Verify the serial number format (SQ + 11 characters)
4. Restart the application if connection fails
5. Check the Windows Event Viewer for BLE-related errors

