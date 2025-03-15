from	machine		import	SPI, Pin, Timer
from	utime		import	sleep, sleep_ms, sleep_us
from	struct		import	unpack
from	micropython	import	schedule
from nxp_periph.interface	import	SPI_target
from nxp_periph.MikanUtil	import	MikanUtil

WAIT	= 0.001
#WAIT	= 0
CWAIT	= 0

def main():
	spi	= SPI( 0, 1000_000, cs = 0, phase = 1 )

	afe	= NAFE13388( spi, None )
	
	sleep_ms( 250 )	#	wait for first DIE_TEMP register update
	afe.dump( [ 0x7C, 0x7D, 0x7E, 0xAE, 0xAF, 0x34, 0x37, None, 0x30, 0x31 ] )
	
	count	= 0

	sleep(0.5)
	afe.logical_ch_config( 0, [ 0x1710, 0x007C, 0x4E00, 0x0000 ] ),
	afe.logical_ch_config( 1, [ 0x2710, 0x007C, 0x4E00, 0x0000 ] ),

	data	= [ 0 ] * 2

	while True:
		data[ 0 ]	= afe.measure( 0 )
		data[ 1 ]	= afe.measure( 1 )
		
		print( f"read data {data[ 0 ]}, {data[ 1 ]}" )

class AFE_base:
	"""
	An abstraction class to make user interface.
	"""
	pass

class NAFE13388( AFE_base, SPI_target ):
	"""
	NAFE13388: Analog Front-End
	
	A device class for a 8 channel AFE
	This class enables to get its measured voltage
	
	"""
	ch_cnfg_reg	= [ 0x0020, 0x0021, 0x0022, 0x0023 ]
	pga_gain	= [ 0.2, 0.4, 0.8, 1, 2, 4, 8, 16 ]

	REG_DICT	= {
		"CMD_CH0":			0x0000,
		"CMD_CH1":			0x0001,
		"CMD_CH2":			0x0002,
		"CMD_CH3":			0x0003,
		"CMD_CH4":			0x0004,
		"CMD_CH5":			0x0005,
		"CMD_CH6":			0x0006,
		"CMD_CH7":			0x0007,
		"CMD_CH8":			0x0008,
		"CMD_CH9":			0x0009,
		"CMD_CH10":			0x000A,
		"CMD_CH11":			0x000B,
		"CMD_CH12":			0x000C,
		"CMD_CH13":			0x000D,
		"CMD_CH14":			0x000E,
		"CMD_CH15":			0x000F,
		"CMD_ABORT":		0x0010,
		"CMD_END":			0x0011,
		"CMD_CLEAR_ALARM":	0x0012,
		"CMD_CLEAR_DATA":	0x0013,
		"CMD_RESET":		0x0014,
		"CMD_CLEAR_REG":	0x0015,
		"CMD_RELOAD":		0x0016,
		"TBD":				0x0017,
		"CMD_SS":			0x2000,
		"CMD_SC":			0x2001,
		"CMD_MM":			0x2002,
		"CMD_MC":			0x2003,
		"CMD_MS":			0x2004,
		"CMD_BURST_DATA":		0x2005,
		"CMD_CALC_CRC_CONFG":	0x2006,
		"CMD_CALC_CRC_COEF":	0x2007,
		"CMD_CALC_CRC_FAC":		0x2008,
		"CH_CONFIG0":		0x20,
		"CH_CONFIG1":		0x21,
		"CH_CONFIG2":		0x22,
		"CH_CONFIG3":		0x23,
		"CH_CONFIG4":		0x24,
		"CRC_CONF_REGS":	0x25,
		"CRC_COEF_REGS":	0x26,
		"CRC_TRIM_REGS":	0x27,
		"GPI_DATA":	0x29,
		"GPIO_CONFIG0":		0x2A,
		"GPIO_CONFIG1":		0x2B,
		"GPIO_CONFIG2":		0x2C,
		"GPI_EDGE_POS":		0x2D,
		"GPI_EDGE_NEG":		0x2E,
		"GPO_DATA":			0x2F,
		"SYS_CONFIG0":		0x30,
		"SYS_STATUS0":		0x31,
		"GLOBAL_ALARM_ENABLE":	0x32,
		"GLOBAL_ALARM_INTERRUPT":	0x33,
		"DIE_TEMP":			0x34,
		"CH_STATUS0":		0x35,
		"CH_STATUS1":		0x36,
		"THRS_TEMP":		0x37,
		"CH_DATA0":			0x40,
		"CH_DATA1":			0x41,
		"CH_DATA2":			0x42,
		"CH_DATA3":			0x43,
		"CH_DATA4":			0x44,
		"CH_DATA5":			0x45,
		"CH_DATA6":			0x46,
		"CH_DATA7":			0x47,
		"CH_DATA8":			0x48,
		"CH_DATA9":			0x4A,
		"CH_DATA10":		0x4B,
		"CH_DATA11":		0x4C,
		"CH_DATA13":		0x4D,
		"CH_DATA14":		0x4E,
		"CH_DATA15":		0x4F,
		"CH_CONFIG5_0":		0x50,
		"CH_CONFIG5_1":		0x51,
		"CH_CONFIG5_2":		0x52,
		"CH_CONFIG5_3":		0x53,
		"CH_CONFIG5_4":		0x54,
		"CH_CONFIG5_5":		0x55,
		"CH_CONFIG5_6":		0x56,
		"CH_CONFIG5_7":		0x57,
		"CH_CONFIG5_8":		0x58,
		"CH_CONFIG5_9":		0x59,
		"CH_CONFIG5_10":	0x5A,
		"CH_CONFIG5_11":	0x5B,
		"CH_CONFIG5_12":	0x5C,
		"CH_CONFIG5_13":	0x5D,
		"CH_CONFIG5_14":	0x5E,
		"CH_CONFIG5_15":	0x5F,
		"CH_CONFIG6_0":		0x60,
		"CH_CONFIG6_1":		0x61,
		"CH_CONFIG6_2":		0x62,
		"CH_CONFIG6_3":		0x63,
		"CH_CONFIG6_4":		0x64,
		"CH_CONFIG6_5":		0x65,
		"CH_CONFIG6_6":		0x66,
		"CH_CONFIG6_7":		0x67,
		"CH_CONFIG6_8":		0x68,
		"CH_CONFIG6_9":		0x69,
		"CH_CONFIG6_10":	0x6A,
		"CH_CONFIG6_11":	0x6B,
		"CH_CONFIG6_12":	0x6C,
		"CH_CONFIG6_13":	0x6D,
		"CH_CONFIG6_14":	0x6E,
		"CH_CONFIG6_15":	0x6F,
		"PN2":				0x7C,
		"PN1":				0x7D,
		"PN0":				0x7E,
		"CRC_TRIM_INT":		0x7F,
		"GAIN_COEFF0":		0x80,
		"GAIN_COEFF1":		0x81,
		"GAIN_COEFF2":		0x82,
		"GAIN_COEFF3":		0x83,
		"GAIN_COEFF4":		0x84,
		"GAIN_COEFF5":		0x85,
		"GAIN_COEFF6":		0x86,
		"GAIN_COEFF7":		0x87,
		"GAIN_COEFF8":		0x88,
		"GAIN_COEFF9":		0x89,
		"GAIN_COEFF10":		0x8A,
		"GAIN_COEFF11":		0x8B,
		"GAIN_COEFF12":		0x8C,
		"GAIN_COEFF13":		0x8D,
		"GAIN_COEFF14":		0x8E,
		"GAIN_COEFF15":		0x8F,
		"OFFSET_COEFF0":	0x90,
		"OFFSET_COEFF1":	0x91,
		"OFFSET_COEFF2":	0x92,
		"OFFSET_COEFF3":	0x93,
		"OFFSET_COEFF4":	0x94,
		"OFFSET_COEFF5":	0x95,
		"OFFSET_COEFF6":	0x96,
		"OFFSET_COEFF7":	0x97,
		"OFFSET_COEFF8":	0x98,
		"OFFSET_COEFF9":	0x99,
		"OFFSET_COEFF10":	0x9A,
		"OFFSET_COEFF11":	0x9B,
		"OFFSET_COEFF12":	0x9C,
		"OFFSET_COEFF13":	0x9D,
		"OFFSET_COEFF14":	0x9E,
		"OFFSET_COEFF15":	0x9F,
		"OPT_COEF0":		0xA0,
		"OPT_COEF1":		0xA1,
		"OPT_COEF2":		0xA2,
		"OPT_COEF3":		0xA3,
		"OPT_COEF4":		0xA4,
		"OPT_COEF5":		0xA5,
		"OPT_COEF6":		0xA6,
		"OPT_COEF7":		0xA7,
		"OPT_COEF8":		0xA8,
		"OPT_COEF9":		0xA9,
		"OPT_COEF10":		0xAA,
		"OPT_COEF11":		0xAB,
		"OPT_COEF12":		0xAC,
		"OPT_COEF13":		0xAD,
		"SERIAL1":			0xAE,
		"SERIAL0":			0xAF,
	}


	def __init__( self, spi, cs = None ):
		"""
		NAFE13388 initializer
	
		Parameters
		----------
		spi		: machine.SPI instance
		cs		: machine.Pin instance

		"""
		self.tim_flag	= False
		self.cb_count	= 0

		SPI_target.__init__( self, spi, cs )

		"""
		###	For original EVB
		self.reset_pin	= Pin( "D6", Pin.OUT )
		self.syn_pin	= Pin( "D5", Pin.OUT )
		self.drdy_pin	= Pin( "D3", Pin.IN )
		self.int_pin	= Pin( "D2", Pin.IN )
		"""

		###	For UIM
		self.reset_pin	= Pin( "D7", Pin.OUT )
		self.syn_pin	= Pin( "D6", Pin.OUT )
		self.drdy_pin	= Pin( "D4", Pin.IN )
		self.int_pin	= Pin( "D3", Pin.IN )

		
		self.reset_pin.value( 1 )
		self.syn_pin.value( 1 )
		
		self.boot()
		self.reset()
		
		self.coeff_microvolt	= [ 0 ] * 16
		

	def boot( self ):
		"""
		Boot-up procedure
		"""
		self.reg( "CMD_ABORT" )

	def reset( self, hardware_reset = False ):
		"""
		Reset procedure
		"""
		
		if hardware_reset:
			self.reset_pin.value( 0 )
			sleep_ms( 1 )
			self.reset_pin.value( 1 )
		else:
			self.reg( "CMD_RESET" )
	
		retry	= 10
	
		while retry:
			sleep_ms( 3 )
			
			if self.reg( "SYS_STATUS0" ) & (0x1 << 13):
				return;
			
			retry	-= 1
			
		print( "NAFE13388 couldn't get ready. Check power supply or pin conections\r\n" );

		while True:
			pass
	
	def dump( self, list ):
		"""
		Register dump

		Parameters
		----------
		list : list
			List of register address/pointer.
		"""
		for r in list:
			if r:
				print( "0x{:04X} = {:06X}".format( r, self.reg( r ) ) )
			else:
				print( "" )

	def logical_ch_config( self, logical_channel, list ):
		"""
		Logical channel configuration

		Parameters
		----------
		list : list
			List of register values for register 0x20, 0x21, 0x22 and 0x23
			
		"""

		print(  "" )
		print( f"logical_ch_config for {logical_channel}" )

		self.reg( self.REG_DICT["CMD_CH0"] + logical_channel )

		for r, v in zip( self.ch_cnfg_reg, list ):
			self.reg( r, v )
			
		self.dump( self.ch_cnfg_reg )
		
		mask	= 1
		bits	= self.reg( "CH_CONFIG4" ) | mask << logical_channel
		self.reg( "CH_CONFIG4", bits )
		
		print( f"bits = {bits}" )
		print( f"self.reg( 'CH_CONFIG4' ) = {self.reg( 'CH_CONFIG4' )}" )
		
		cc0	= list[ 0 ]
		
		if cc0 & 0x0010:
			self.coeff_microvolt[ logical_channel ]	= ((10.0 / (1 << 24)) / self.pga_gain[ (cc0 >> 5) & 0x7 ]) * 1e6
		else:
			self.coeff_microvolt[ logical_channel ]	= (4.0 / (1 << 24)) * 1e6;

		self.num_logcal_ch	= 0
		
		for i in range( 16 ):
			if bits & (mask << i):
				self.num_logcal_ch	+= 1
		
		print( f"self.num_logcal_ch = {self.num_logcal_ch}" )
		
	def measure( self, ch = None ):
		"""
		Measure input voltage

		Parameters
		----------
		ch : int
			Logical input channel number or None
			
		Returns
		-------
		float in voltage (microvolt) if "ch" was given
		list of raw measured values if "ch" was not given

		"""
		if ch is not None:
			self.reg( self.REG_DICT["CMD_CH0"] + ch )
			self.reg( "CMD_SS" )
#			sleep_ms( 100 )
			sleep_ms( 50 )
			return self.reg( self.REG_DICT["CH_DATA0"] + ch ) * self.coeff_microvolt[ ch ]
		
		values	= []

		command	= "CMD_MS"

		for i in range( self.num_logcal_ch ):
			self.write_r16( command )
			"""
			print( f"after command" )
			for i in range( 100 ):
				print( f"0x31 = {self.read_r16( 0x31 ):04X}" )
				sleep_us( 10 )
			"""
			sleep_ms( 10 )
			values	+= [ self.read_r24( self.REG_DICT["CH_DATA0"] + i ) ]
		
		print( values )

		return values
		
	def read( self, ch = None ):
		"""
		Read input value

		Parameters
		----------
		ch : int
			Logical input channel number or None
			This part need to be implemented
			
		Returns
		-------
		list of raw measured values if "ch" was not given

		"""
		values	= []

		for i in range( self.num_logcal_ch ):
			values	+= [ self.read_r24( 0x2040 + i ) ]
		
		print( values )

		return values
	
	def die_temp( self ):
		"""
		Die temperature
		
		Returns
		-------
		float : Die temperature in celcius

		"""
		return self.read_r16( 0x34, signed = True ) / 64

	def reg( self, reg, value = None ):
		"""
		register access read/write
		data bit length (24 or 16) is auto selected by register name/address
	
		Parameters
		----------
		reg : string or int
			Register name or register address/pointer.
		val : int
			Register is written if val is available
			Register is read if val is not available
			
		"""
		reg	= self.REG_DICT[ reg ] if type( reg ) != int else reg

		bit_width	= 24

#		print( f"reg# = 0x{reg:04X}" )

		if (((reg >> 4) & 0xF) < 0x4) or (((reg >> 4) & 0xF) == 0x7):
			bit_width	= 16

		if (((reg >> 4) & 0xF) < 0x2):
			bit_width	= 0

#		print( f"reg# = 0x{reg:04X} (w:{bit_width})" )


		if (value is not None) or (bit_width == 0):
			if bit_width == 24:
				self.write_r24( reg, value )
			else:
				self.write_r16( reg, value )
		else:
			if bit_width == 24:
				return self.read_r24( reg )
			else:
				return self.read_r16( reg )
	
	def	write_r16( self, reg, val = None ):
		"""
		writing 16bit register
	
		Parameters
		----------
		reg : int
			Register address/pointer.
		val : int
			16bit data
			
		"""
		reg		<<= 1
	
		regH	= reg >> 8 & 0xFF
		regL	= reg & 0xFF

		if val is None:
			self.send( [ regH, regL ] )
		else:
			valH	= val >> 8 & 0xFF
			valL	= val      & 0xFF
			self.send( [ regH, regL, valH, valL ] )

	def	write_r24( self, reg, val = None ):
		"""
		writing 16bit register
	
		Parameters
		----------
		reg : int
			Register address/pointer.
		val : int
			16bit data
			
		"""
		reg		<<= 1
	
		regH	= reg >> 8 & 0xFF
		regL	= reg & 0xFF

		if val is None:
			self.send( [ regH, regL ] )
		else:
			valH	= val >> 16 & 0xFF
			valM	= val >>  8 & 0xFF
			valL	= val       & 0xFF
			self.send( [ regH, regL, valH, valM, valL ] )

	def	read_r16( self, reg, signed = False ):
		"""
		reading 16bit register
	
		Parameters
		----------
		reg : int
			Register address/pointer.
		signed : bool
			Switch to select the data in signed or unsigned (default: signed)
			
		Returns
		-------
		int : register value

		"""
		reg		<<= 1
		reg		|= 0x4000
		regH	= reg >> 8 & 0xFF
		regL	= reg & 0xFF

		data	= bytearray( [ regH, regL, 0xFF, 0xFF ] )
		self.__if.write_readinto( data, data )
		
		return unpack( ">h" if signed else ">H", data[2:] )[ 0 ]

	def	read_r24( self, reg ):
		"""
		reading 24bit register
	
		Parameters
		----------
		reg : int
			Register address/pointer.
			
		Returns
		-------
		int : register value

		"""
		reg		<<= 1
		reg		|= 0x4000
		regH	= reg >> 8 & 0xFF
		regL	= reg & 0xFF

		data	= bytearray( [ regH, regL, 0xFF, 0xFF, 0xFF ] )
		self.__if.write_readinto( data, data )

		data	+= b'\x00'		
		data	= unpack( ">l", data[2:] )[ 0 ] >> 8

		return data

if __name__ == "__main__":
	main()
