"""
Demonstrates setting up stream-in and stream-out together, then reading
stream-in values.

Connect a wire from AIN0 to DAC0 to see the effect of stream-out on
stream-in channel 0.

Relevant Documentation:

LJM Library:
    LJM Library Installer:
        https://labjack.com/support/software/installers/ljm
    LJM Users Guide:
        https://labjack.com/support/software/api/ljm
    Opening and Closing:
        https://labjack.com/support/software/api/ljm/function-reference/opening-and-closing
    NamesToAddresses:
        https://labjack.com/support/software/api/ljm/function-reference/utility/ljmnamestoaddresses
    eWriteName:
        https://labjack.com/support/software/api/ljm/function-reference/ljmewritename
    Stream Functions (eStreamRead, eStreamStart, etc.):
        https://labjack.com/support/software/api/ljm/function-reference/stream-functions

T-Series and I/O:
    Modbus Map:
        https://labjack.com/support/software/api/modbus/modbus-map
    Stream Mode:
        https://labjack.com/support/datasheets/t-series/communication/stream-mode
    Analog Inputs:
        https://labjack.com/support/datasheets/t-series/ain
    Stream-Out:
        https://labjack.com/support/datasheets/t-series/communication/stream-mode/stream-out/stream-out-description
    Digital I/O:
        https://labjack.com/support/datasheets/t-series/digital-io
    DAC:
        https://labjack.com/support/datasheets/t-series/dac

"""
from datetime import datetime
import sys
import time
import collections
import pandas as pd
from labjack import ljm

def run_labjack(file,MAX_REQUESTS):
    #log string to store log information
    log = ''
    # The number of eStreamRead calls that will be performed.

    # Open first found LabJack
    handle = ljm.openS("ANY", "ANY", "ANY")  # Any device, Any connection, Any identifier
    # handle = ljm.openS("T7", "ANY", "ANY")  # T7 device, Any connection, Any identifier
    # handle = ljm.openS("T4", "ANY", "ANY")  # T4 device, Any connection, Any identifier
    # handle = ljm.open(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")  # Any device, Any connection, Any identifier

    info = ljm.getHandleInfo(handle)
    log+= ("Opened a LabJack with Device type: %i, Connection type: %i,\n"
          "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i\n" %
          (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

    deviceType = info[0]

    # Setup Stream Out
    OUT_NAMES = ["DAC0"]
    NUM_OUT_CHANNELS = len(OUT_NAMES)
    outAddress = ljm.nameToAddress(OUT_NAMES[0])[0]

    # Allocate memory for the stream-out buffer
    ljm.eWriteName(handle, "STREAM_OUT0_TARGET", outAddress)
    ljm.eWriteName(handle, "STREAM_OUT0_BUFFER_SIZE", 512)
    ljm.eWriteName(handle, "STREAM_OUT0_ENABLE", 1)

    # Write values to the stream-out buffer
    ljm.eWriteName(handle, "STREAM_OUT0_LOOP_SIZE", 6)
    ljm.eWriteName(handle, "STREAM_OUT0_BUFFER_F32", 0.0)  # 0.0 V
    ljm.eWriteName(handle, "STREAM_OUT0_BUFFER_F32", 1.0)  # 1.0 V
    ljm.eWriteName(handle, "STREAM_OUT0_BUFFER_F32", 2.0)  # 2.0 V
    ljm.eWriteName(handle, "STREAM_OUT0_BUFFER_F32", 3.0)  # 3.0 V
    ljm.eWriteName(handle, "STREAM_OUT0_BUFFER_F32", 4.0)  # 4.0 V
    ljm.eWriteName(handle, "STREAM_OUT0_BUFFER_F32", 5.0)  # 5.0 V
    ljm.eWriteName(handle, "STREAM_OUT0_SET_LOOP", 1)

    log += ("STREAM_OUT0_BUFFER_STATUS = %f\n" % (ljm.eReadName(handle, "STREAM_OUT0_BUFFER_STATUS")))

    # Stream Configuration
    POS_IN_NAMES = ["AIN0", "AIN2"]
    NUM_IN_CHANNELS = len(POS_IN_NAMES)

    TOTAL_NUM_CHANNELS = NUM_IN_CHANNELS + NUM_OUT_CHANNELS

    # Add positive channels to scan list
    aScanList = ljm.namesToAddresses(NUM_IN_CHANNELS, POS_IN_NAMES)[0]
    scanRate = 2000
    scansPerRead = 60

    # Add the scan list outputs to the end of the scan list.
    # STREAM_OUT0 = 4800, STREAM_OUT1 = 4801, etc.
    aScanList.extend([4800])  # STREAM_OUT0
    # If we had more STREAM_OUTs
    # aScanList.extend([4801])  # STREAM_OUT1
    # aScanList.extend([4802])  # STREAM_OUT2
    # aScanList.extend([4803])  # STREAM_OUT3

    try:
        # When streaming, negative channels and ranges can be configured for
        # individual analog inputs, but the stream has only one settling time and
        # resolution.

        if deviceType == ljm.constants.dtT4:
            # LabJack T4 configuration

            # AIN0 and AIN1 ranges are +/-10 V, stream settling is 0 (default) and
            # stream resolution index is 0 (default).
            aNames = ["AIN0_RANGE", "AIN2_RANGE", "STREAM_SETTLING_US",
                      "STREAM_RESOLUTION_INDEX"]
            aValues = [10.0, 10.0, 0, 0]
        else:
            # LabJack T7 and other devices configuration

            # Ensure triggered stream is disabled.
            ljm.eWriteName(handle, "STREAM_TRIGGER_INDEX", 0)

            # Enabling internally-clocked stream.
            ljm.eWriteName(handle, "STREAM_CLOCK_SOURCE", 0)

            # All negative channels are single-ended, AIN0 and AIN1 ranges are
            # +/-10 V, stream settling is 0 (default) and stream resolution index
            # is 0 (default).
            aNames = ["AIN_ALL_NEGATIVE_CH", "AIN0_RANGE", "AIN2_RANGE",
                      "STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"]
            aValues = [ljm.constants.GND, 10.0, 10.0, 0, 0]
        # Write the analog inputs' negative channels (when applicable), ranges,
        # stream settling time and stream resolution configuration.
        numFrames = len(aNames)
        ljm.eWriteNames(handle, numFrames, aNames, aValues)

        # Configure and start stream
        log += str(aScanList[0:TOTAL_NUM_CHANNELS]) +'\n'
        scanRate = ljm.eStreamStart(handle, scansPerRead, TOTAL_NUM_CHANNELS, aScanList, scanRate)
        log += ("\nStream started with a scan rate of %0.0f Hz.\n" % scanRate)

        log += ("\nPerforming %i stream reads.\n" % MAX_REQUESTS)
        start = datetime.now()
        totScans = 0
        totSkip = 0  # Total skipped samples

        i = 1

        scan_number = 0
        raw_data = collections.defaultdict(list)
        while i <= MAX_REQUESTS:
            ret = ljm.eStreamRead(handle)

            # Note that the Python eStreamData will return a data list of size
            # scansPerRead*TOTAL_NUM_CHANNELS, but only the first
            # scansPerRead*NUM_IN_CHANNELS samples in the list are valid. Output
            # channels are not included in the eStreamRead's returned data.
            data = ret[0][0:(scansPerRead * NUM_IN_CHANNELS)]
            scans = len(data) / NUM_IN_CHANNELS
            totScans += scans

            # Count the skipped samples which are indicated by -9999 values. Missed
            # samples occur after a device's stream buffer overflows and are
            # reported after auto-recover mode ends.
            curSkip = data.count(-9999.0)
            totSkip += curSkip


            log += ("\neStreamRead #%i, %i scans\n" % (i, scans))
            readStr = "  "
            for j in range(0, scansPerRead):
                raw_data['Time'].append(datetime.now()-start)
                for k in range(0, NUM_IN_CHANNELS):
                    readStr += "%s: %0.5f, " % (POS_IN_NAMES[k], data[j * NUM_IN_CHANNELS + k])
                    raw_data[POS_IN_NAMES[k]].append(data[j * NUM_IN_CHANNELS + k])
                readStr += "\n  "
                scan_number+=1
                raw_data['ScanNumber'].append(scan_number)
                raw_data['ScanBlock'].append(i)

            readStr += "Scans Skipped = %0.0f, Scan Backlogs: Device = %i, LJM = %i" % \
                       (curSkip / NUM_IN_CHANNELS, ret[1], ret[2])
            log += (readStr)+'\n'
            i += 1

        end = datetime.now()
        log += ("\nTotal scans = %i\n" % (totScans))
        tt = (end - start).seconds + float((end - start).microseconds) / 1000000
        log += ("Time taken = %f seconds\n" % (tt))
        log += ("LJM Scan Rate = %f scans/second\n" % (scanRate))
        log += ("Timed Scan Rate = %f scans/second\n" % (totScans / tt))
        log += ("Timed Sample Rate = %f samples/second\n" % (totScans * NUM_IN_CHANNELS / tt))
        log += ("Skipped scans = %0.0f\n" % (totSkip / NUM_IN_CHANNELS))
    except ljm.LJMError:
        ljme = sys.exc_info()[1]
        log+=(ljme)
    except Exception:
        e = sys.exc_info()[1]
        log+=(e)

    try:
        log += ("\nStop Stream\n")
        ljm.eStreamStop(handle)
    except ljm.LJMError:
        ljme = sys.exc_info()[1]
        log+=(ljme)
    except Exception:
        e = sys.exc_info()[1]
        log+=(e)

    # Close handle
    ljm.close(handle)

    raw_dataframe=pd.DataFrame.from_dict(raw_data)
    raw_dataframe.to_csv(file+'-data.csv',index=False)
    with open(file+'-log.txt', "w") as log_file:
        log_file.write(log)
