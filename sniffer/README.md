Tiny BLE as a BLE Sniffer
=========================

1. Get nRF Sniffer resource from [Nordic Semiconductor](https://www.nordicsemi.com/eng/Products/Bluetooth-Smart-Bluetooth-low-energy/nRF-Sniffer)



2. download the firmware of nRF Sniffer into the Tiny BLE.

3. Replace the interface firmware of Tiny BLE  with the [usb_to_uart_firmware.bin](usb_to_uart_firmware.bin) file.

  As the USB virtual serial's performance of the default firmware is not good enough, we need replace a new firmware.

  a. hold the button of the Tiny BLE and plug it into your computer.
  b. replace the firmware.bin file of a disk named `CRP DISABLD` with the usb_to_uart_firmware.bin file. If Linux/Mac is used, use the`sudo dd if={/path/to/usb_to_uart_firmware.bin} of={/path/to/firmware.bin} conv=notrunc` command.
  c. re-plug it into the computer. If windows is used, install the usb_to_uart_driver.inf driver.

4. If windows is used, use the BLE Sniffer application from Nordic Semiconductor. If Mac OS X is used, [nrf-ble-sniffer-osx](https://sourceforge.net/projects/nrfblesnifferosx/) is good choice.