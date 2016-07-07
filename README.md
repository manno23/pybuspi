# PyBusPi - interactive spi 
    
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
