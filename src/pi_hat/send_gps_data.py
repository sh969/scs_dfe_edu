import serial
import time
import json
import datetime
import pynmea2
from at_commands import *

ser = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=5)

time.sleep(5)
APN = 'TM'
URL = 'www.ppp.one/gps.php'

dataframe = {
		"datetime" : None,
		"lat" : None,
		"lon" : None,
		"alt" : None,
		"vel" : None,
		"hhop" : None
	}


print("gps off")
GPSoff(ser)
print("gprs_on")
GPRSstartup(ser, APN, URL)
print("gps_on")
GPSstartup(ser)



while 1:
    # Start GNSS data received via UART
    txrx_force(ser, 'AT+CGNSTST=1\r\n', 'OK', 5)
    # Get one dataframe (see above) from GNSS string
    dataframe = readGPS(ser, dataframe)          
    # Stop GNSS data received via UART so you can send data via GPRS    
    txrx_force(ser, 'AT+CGNSTST=0\r\n', 'OK', 5)
    
    # Prep send
    txrx_force(ser, 'AT+HTTPDATA='+ str(len(json.dumps(dataframe)))+',10000\r\n', 'DOWNLOAD', 5)
    # Load data
    txrx_force(ser, json.dumps(dataframe) + '\r\n', 'OK', 5)    
    # Post the data
    txrx_force(ser, 'AT+HTTPACTION=1\r\n', '+HTTPACTION: 1,200,1', 5)

    print(json.dumps(dataframe))
    
    #Read the response
    #txrx_force(ser, 'AT+HTTPREAD\r\n', '1', 5)
    
    #time.sleep(1)