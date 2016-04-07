import serial, binascii

"""
    PyBusPi - interactive spi 

    Made to use interactively, so can modularly construct actions to write to spi flash however you wish.
    This was a very helpful tool for me to use in conjunction with the official flashrom program.


    >> import bp
    >> bp.open("/dev/ttyUSB0")
    >> bp.read_page(0x7fff00)

    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00
     \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00
     \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00
     \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x004.0\x00LENOVO\x00
     ThinkPad X200\x00\xa9\x00\x00\x00\xa5\x00\x00\x00\x9e\x00\x00 \x00\x00\x00\x80
     \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00
     \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00
     \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00
     \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00
     \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe95\xfa\xff\xff\x00\x00
     \x00\xe9\x97\xfa\xff\x08\xfa\xff\xff'



    # Read in the rom image to file and use the included utilities to program specified sections.

    >> rom_image = file('a+', 'bios_rom.img')
    >> bp.program(rom_image, 0, 0x10000)


 """



##################################################
#####     Python BusPirate SPI Interface     #####
##################################################

serial_port = None

def open(dev="/dev/ttyUSB0", spispeed='1M', baudrate=115200, timeout=1.5):
    """
    Initialises the serial port then enters the Bus Pirate into raw SPI mode
    with a default configuration.

    Args: 
        baudrate: The baudrate applied to the usb serial port.
        timeout:  This is the time the serial port will wait on the buffer before yielding.

    """
    global serial_port
    serial_port = serial.PosixPollSerial(port=dev, baudrate=baudrate, timeout=timeout)
    
    serial_port.write('\x00'*20) # Enter Bitbang mode from the initial BP mode.
    serial_port.read(20*5)       # Blocking read here to make sure all data is cleared, 
                                 # the response can be slow.

    enter_bitbang_mode()    
    enter_spi_mode()

    setc(SPI_CONF)               # set default configuration
    setp(PERIPH_CONF)
    set_spi_speed(spispeed)


def close():
    enter_bitbang_mode()
    restart_buspirate()

    serial_port.close()
    print 'buspirate reset.'



##################################################
#####           BusPirate Protocol          ######
##################################################

def enter_bitbang_mode():
    """ exits raw serial_port mode back into bitbang mode. assumes we are in bitbang or raw spi mode. """
    serial_port.write('\x00')
    validate("entered bitbang mode", "failed to enter bitbang mode", 'BBIO1')

def enter_spi_mode():
    """ enter raw spi mode. assumes we are in bitbang mode. """
    serial_port.write('\x01')
    validate("entered spi mode", "error returning spi version string", 'SPI1')

def restart_buspirate():
    """ resets the state of the buspirate and goes back to default shell. """
    serial_port.write('\x0f')

def cs_low():
    """ sets the cs pin low. """
    serial_port.write('\x02')
    validate(" / ", "error putting cs low")

def cs_high():
    """ sets the cs pin high. """
    serial_port.write('\x03')    
    validate(" \\ ", "error putting cs high")


def spi_cmd(data, read_count=0, raw=True):
    """ 
    Sets the CS pin low then sends all data bytes to the SPI.
    @read_count: sends this number of clock signals to the spi to gather the response.
    @raw:        if set true does not include setting of the cs pin

    """
    if raw: 
        buffer = '\x04'
    else:
        buffer = '\x05'
    write_count = len(data)
    buffer += pack(write_count, 2)
    buffer += pack(read_count, 2)
    buffer += data
    serial_port.write(buffer)

    validate("", "buspirate command failed")
    return serial_port.read(read_count)


def validate(success_msg, error_msg, expected_response='\x01'):
    """ 
    Compares the expected response against the response received.
    Most commands default to a response of '\x01' on success. 
    """
    response = serial_port.read(len(expected_response))

    if response != expected_response: 
        raise Exception(error_msg)
    else:
        print success_msg


# Bus-Pirate SPI Configuration
spi_3v3 =         0b1000  # hiz \ 3.3v
spi_clk_idle_hi = 0b0100  # clock idle low \ high
spi_oclke_a2i =   0b0010  # output clock edge idle-active \ active-idle
spi_smp_end =     0b0001  # sample-time middle \ end

SPI_CONF = spi_3v3 | spi_oclke_a2i | spi_smp_end 

def setc(value):
    """
    sets the spi configuration of the buspirate.

    spi_3v3:        pin mode           -   hiz | 3.3v
    spi_idle_hi:    clock idle state   -   low | high
    spi_oclke_a2i:  output clock edge  -   idle->active | active->idle
    spi_smp_end:    input sample phase -   middle | end

    output clock edge - idle to active, active to idle. point at which data is changed on the sdo line, this does not
    include the msb (first bit) which is ready immediately after cs becomes active.

    output type - open drain/open collector (high=hi-z, low=ground) , normal (high=3.3volts, low=ground). use open
    drain/open collector output types with pull-up resistors for multi-voltage interfacing. 

    """
    serial_port.write( pack( 0x80 | value , 1) )
    validate('set configuration: %s' % hex(0x80 | value), "error setting the configuration")


# Bus-Pirate Pin Configuration
pin_pwr_on =     0b1000  # power supply off \ on
pin_pullups_on = 0b0100  # pullups off \ on
pin_aux_high =   0b0010  # auxillarypin off \ on
pin_cs_idle_hi = 0b0001  # cs-pin idle low \ high 

PERIPH_CONF = pin_cs_idle_hi 

def setp(value):
    # pwr: off|on  # pup: off|on  # aux: 0v|3.3v  # cs : l|h
    serial_port.write( pack( 0x40 | value , 1) )
    validate('set peripherals: %s' % hex(0x40 | value), "error setting peripherals.")

def set_spi_speed(spi_speed):
    if   spi_speed == '30K':  val = '\x60'
    elif spi_speed == '125K': val = '\x61'
    elif spi_speed == '250K': val = '\x62'
    elif spi_speed == '1M':   val = '\x63'
    elif spi_speed == '2M':   val = '\x64'
    elif spi_speed == '4M':   val = '\x66'
    elif spi_speed == '8M':   val = '\x67'
    else: raise Exception("can only use supported values for spi_speed.")
    serial_port.write(val)
    validate('set SPI spi_speed to %sHz' % spi_speed, "Error setting SPI spi_speed on Bus Pirate.")
 

# Unimplemented 
# * 0001xxxx - Bulk SPI transfer, send 1-16 bytes (0=1byte!)
# * 00000110 - AVR Extended Commands
# * 00000000 - Null operation - verifies extended commands are available.
# * 00000001 - Return version (2 bytes)
# * 00000010 - Bulk Memory Read from Flash



##################################################
#####              SPI Commands              #####
##################################################

""" 
    # WREN  06 (write enable) 
    # WRDI  04 (write disable)
    # RDID  9F (read identification)
    # RDSR  05 (read status register)
    # WRSR  01 (write status register)
    # READ  03 (read data)
    # FAST-READ  0b (fast read data)
    # SECTOR-ERASE 20 aa bb cc sector is 0x000 - 0xFFF address range
    # BLOCK-ERASE D8 aa bb cc block is 16 sectors, 0x0000 - 0xFFFF
    # CHIP-ERASE 60 | C7 
    # PAGE-PROGRAM 02 aa bb cc programs the selected page 0xaabb00 - 0xaabbFF
    # DEEP-POWER-DOWN                B9
    # Release from DEEP-POWER-DOWN   AB
    # READ-DEVICE-ID AB xx xx xx returns 1 byte

    # REMS 90 xx xx aa
    read manufacturer and device id
    if aa=00 manufacturer id first
    if aa=01 device id first
"""

def write_enable():
    spi_cmd('\x06', 0)

def write_disable():
    spi_cmd('\x04', 0)

def read_status():
    status = spi_cmd('\x05', 1)
    return status

def read_page(address):
    cmd = '\x03' + pack(address, 3)
    return spi_cmd(cmd, 256)

def write_page(rom, address):
    cmd = '\x02' + pack(address, 3) + rom_page(rom, address)
    write_enable()
    spi_cmd(cmd, 0)

def write_sector(rom, address):
    for page in xrange(address, address+256*16, 256):
        write_page(rom, page)

def erase_sector(address):
    cmd = '\x20' + pack(address, 3)
    write_enable()
    spi_cmd(cmd, 0)






##################################################
#####                Utilities               #####
##################################################

PAGE_SIZE = 256
SECTOR_SIZE = PAGE_SIZE*16

def program(rom, start, end):
    for sector in xrange(start, end, SECTOR_SIZE):
        try:
            if not check_sector(rom, sector):
                print 'Erasing sector', hex(sector)
                erase_sector(sector)

                for page in xrange(sector, sector+SECTOR_SIZE, PAGE_SIZE):
                    if rom_page(rom, page) != read_page(page):
                        print 'Writing', hex(page)
                        write_page(rom, page)
        except Exception:
            print "\n Restarting >>>>> \n"
            serial_port.read_all()
            program(rom, sector, end) 


def check_sector(rom, address):
    """
    Compares the pages in the sector against the image to be flashed, 
    returns True if they match, False if they do not match.
    """
    # Check address is a valid sector address
    for x in xrange(address, address+256*16, 256):
        flash_page = read_page(x)
        if rom_page(rom, x) != flash_page:
            return False
    return True

def rom_page(rom, address):
    rom.seek(address)
    return rom.read(256)


def pack(h, n):
    """
    Converts integer to bigendian unicode string representation
    similar to 
        struct.pack('>H', int)
    Though we can map to odd number of bytes here rather than
    mapping to given data types like H=2, B=1, I=4...
    """
    if (h < 0): 
        raise Exception("Cannot be a negative value")
    val = hex(h)[2:]
    diff = n * 2 - len(val)
    if diff < 0:
        raise Exception("Value to big for byte count")
    val = '0'*diff + val
    return binascii.unhexlify(val)


def prettify(s):
    """
    Only 1 of:
    Every 4 characters 1 serial_portace, every 8 characters, every 
    (x,y) for x in (1,2,3,4) for y in (10,15,3,22) if x*y > 25

    ' '.join(x.encode('hex') for x in val [16*n:16*(n+1)-1]+'\n'
    """
    def brk_line(s):
        return '\t' + ' '.join([s[n*2:n*2+2] for n in range(16)])
    return '\n'.join([brk_line(s[32*n:32*(n+1)]) for n in range(8)])


def read_rom(filename, start, end, page_read_count):

    f = open(filename, 'r+')

    for page_addr in xrange(start, end, 256):
        if f.read(256) == '\xff'*256:
            for _ in xrange(page_read_count):
                page = bp.read_page(page_addr)
                if page != '\xff'*256:
                    print 'replacing', hex(page_addr)
                    f.seek(page_addr)
                    f.write(page)
                    break


