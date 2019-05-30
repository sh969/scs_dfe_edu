import serial
import time
import datetime
import pynmea2

APN = 'TM'
URL = 'www.ppp.one/gps.php'

def sim800_respond(port, expected_answer, time_out):
    abort = 0
    answer = False
    response = []
    while answer == False:
        response.append(port.readline().strip().decode('ascii'))
        #print(abort)
        #print(response[-1])
        if (expected_answer in response[-1]) or (abort >= time_out):
            answer = True
        elif "ERROR" in response[-1] and (("AT+HTTPINIT" in response[-2]) or ("AT+SAPBR=1,1" in response[-2])) == 0:
            #print("gps off")
            GPSoff(port)
            #print("gprs_on")
            GPRSstartup(port, APN, URL)
            #print("gps_on")
            GPSstartup(port)
            
        else:
            time.sleep(0.1)
            abort = abort + 1
    return answer
        
def txrx_force(port, text, expected_answer, time_out):
    port.write(text.encode())
    sim800_respond(port, expected_answer, time_out)     
    
def GPRSstartup(port, APN, URL):
    #Reset
    txrx_force(port, 'ATZ\r\n', 'OK', 5)
    time.sleep(1)

    #Check there
    txrx_force(port, 'AT\r\n', 'OK', 5)
    time.sleep(1)
    
    #SIM card inportted and unlocked?
    txrx_force(port, 'AT+CPIN?\r\n', '+CPIN: READY', 5)
    time.sleep(1)
    
    #Is the SIM card registered?
    txrx_force(port, 'AT+CREG?\r\n', '+CREG: 0,1', 5)
    time.sleep(1)
    
    #Is GPRS attached?
    txrx_force(port, 'AT+CGATT?\r\n', '+CGATT: 1', 5)
    time.sleep(1)
    
    #Check signal strength - should be 9 or higher
    txrx_force(port, 'AT+CSQ\r\n', 'OK', 5)
    time.sleep(1)
    
    #Set connection type to GPRS
    txrx_force(port, 'AT+SAPBR=3,1,"Contype","GPRS"\r\n', 'OK', 5)
    time.sleep(1)
    
    #Set the APN - this will depend on your network/portvice provider
    txrx_force(port, 'AT+SAPBR=3,1,"APN","' + APN + '"\r\n', 'OK', 5)
    time.sleep(1)
    
    #Enable GPRS - this will take a moment or two
    txrx_force(port, 'AT+SAPBR=1,1\r\n', 'OK', 10)
    time.sleep(5)
    
    #Check to see if connection is correct and get your IP address
    txrx_force(port, 'AT+SAPBR=2,1\r\n', 'OK', 5)
    time.sleep(1)
    
    #Enable HTTP mode
    txrx_force(port, 'AT+HTTPINIT\r\n', 'OK', 1)
    time.sleep(1)
    
    #Set HTTP profile identifier
    txrx_force(port, 'AT+HTTPPARA="CID",1\r\n', 'OK', 5)
    time.sleep(1)
    
    #Put in the URL of the PHP webpage where you will post
    txrx_force(port, 'AT+HTTPPARA="URL","' + URL + '"\r\n', 'OK', 5)
    time.sleep(1)
    
    #Type of content
    txrx_force(port, 'AT+HTTPPARA="CONTENT","application/json"\r\n', 'OK', 5)
    time.sleep(1)

def GPSstartup(port):
    #Check there
    txrx_force(port, 'AT\r\n', 'OK', 5)
    time.sleep(1)
    
    #Power GPS
    txrx_force(port, 'AT+CGNSPWR=1\r\n', 'OK', 5)
    time.sleep(1)
    
    # Set the baud rate of GPS
    txrx_force(port, 'AT+CGNSIPR=115200\r\n', 'OK', 5)
    time.sleep(1)
    
    # Send data received to UART
    txrx_force(port, 'AT+CGNSTST=1\r\n', 'OK', 5)
    time.sleep(1)
    
    # Print the GPS information
    txrx_force(port, 'AT+CGNSINF\r\n', 'OK', 5)
    time.sleep(1)
    
def GPSoff(port):
    #Un-power GPS
    port.flushInput()
    txrx_force(port, 'AT+CGNSPWR=0\r\n', 'OK', 5)
    time.sleep(1)
    #port.flushInput()
    
def readGPS(port, dataframe):
    check1 = 0
    check2 = 0
    reading = 1
    while reading == 1:
        fd = port.readline().decode('ascii')		# Read the GPS data from UART
        #print(fd)
        
        if '$GNGGA' in fd:	 
            ps=fd.find('$GNGGA')
            ps1=fd[ps:].find('\n')
    
            if ps1 != -1:
                data=fd[ps:ps+ps1]
                msg = pynmea2.parse(data)
                timeS = msg.timestamp
                dataframe["lat"] = msg.latitude; 
                dataframe["lon"] = msg.longitude; 
                dataframe["alt"] = msg.altitude; 
                dataframe["hhop"] = msg.horizontal_dil;
                check1 = 1
                #print(dataframe)
    
        if 'GNRMC' in fd:
            ps=fd.find('$GNRMC')
            ps1=fd[ps:].find('\n')
    
            if ps1 != -1:
                data=fd[ps:ps+ps1]
                msg = pynmea2.parse(data)
                dateS = msg.datestamp
                check2 = 1
                
                
        if 'GNVTG' in fd and check1 and check2:
            check1, check2 = 0,0
            ps=fd.find('$GNVTG')
            ps1=fd[ps:].find('\n')
    
            if ps1 != -1:
                data=fd[ps:ps+ps1]
                msg = pynmea2.parse(data)
                dataframe["vel"] = msg.spd_over_grnd_kmph
                dataframe["datetime"] = str(datetime.datetime.combine(dateS,timeS))
                port.flushInput()
                reading = 0
    return dataframe