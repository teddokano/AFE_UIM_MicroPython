from	machine		import	SPI, Pin, Timer
from	utime		import	sleep, sleep_ms, sleep_us
from	struct		import	unpack
from	micropython	import	schedule
from	nxp_periph.interface	import	SPI_target
from	nxp_periph.MikanUtil	import	MikanUtil
import	os

WAIT	= 0.001
#WAIT	= 0
CWAIT	= 0

def main():
	spi	= SPI( 0, 1_000_000, cs = 0, phase = 1 )

	"""
	while True:
		data	= ( bytearray( [ 0x55, 0xAA ] ) )
		spi.write_readinto( data, data )
		sleep( 0.5 )
	"""

	afe	= NAFE13388( spi, None )
#	afe.blink_leds()
	
	sleep_ms( 250 )	#	wait for first DIE_TEMP register update
	afe.dump( [ "PN2", "PN1", "PN0", "SERIAL1", "SERIAL0", "DIE_TEMP", None, "SYS_CONFIG0", "SYS_STATUS0" ] )
	
	print( f"temp = {afe.die_temp()}℃" )

	count	= 0

	afe.open_logical_channel( 0, [ 0x1710, 0x00BC, 0x4C00, 0x0000 ] )
	afe.open_logical_channel( 1, [ 0x5710, 0x00BC, 0x4C00, 0x0000 ] )
	afe.open_logical_channel( 3, [ 0x0010, 0x00BC, 0x4C00, 0x0000 ] )
	afe.open_logical_channel( 7, [ 0x7710, 0x00BC, 0x4C00, 0x0000 ] )

	afe.info_logical_channel()

	afe.continuous_read_start()

	while True:
		print( f"{afe.data}" )
		sleep( 0.5 )

	while True:
		data	= afe.read_V()

		for v in data:
			print( f"{v}, ", end = "" )
		
		print( f"" )
			


	data	= [ 0 ] * 2

	while True:
		data[ 0 ]	= afe.read_V( 0 )
		data[ 1 ]	= afe.read_V( 1 )
		
		print( f"read data {data[ 0 ]}, {data[ 1 ]}" )

class AFE_Error( Exception ):
	"""
	Just a class for I2C exception handling
	"""
	pass
	
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
	ch_cnfg_reg	= ( 0x0020, 0x0021, 0x0022, 0x0023 )
	pga_gain	= ( 0.2, 0.4, 0.8, 1, 2, 4, 8, 16 )
	data_rates	= (	   288000, 192000, 144000, 96000, 72000, 48000, 36000, 24000, 
						18000,  12000,   9000,  6000,  4500,  3000,  2250,  1125, 
						562.5,    400,    300,   200,   100,    60,    50,    30, 
							25,     20,     15,    10,   7.5, 	)
	delays		= (		0,   2,   4,   6,   8,  10,   12,  14, 
						16,  18,  20,  28,  38,  40,   42,  56, 
						64,  76,  90, 128, 154, 178, 204, 224, 
					   256, 358, 512, 716, 1024, 1664, 3276, 7680, 19200, 23040 )
	delay_accuracy	= 1.1
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
		"GPI_DATA":			0x29,
		"GPIO_CONFIG0":		0x2A,
		"GPIO_CONFIG1":		0x2B,
		"GPIO_CONFIG2":		0x2C,
		"GPI_EDGE_POS":		0x2D,
		"GPI_EDGE_NEG":		0x2E,
		"GPO_DATA":			0x2F,
		"SYS_CONFIG0":		0x30,
		"SYS_STATUS0":		0x31,
		"GLOBAL_ALARM_ENABLE":		0x32,
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
		'''
		if "MIMXRT105" in os.uname().machine:
			self.drdy_pin	= Pin( "D0", Pin.IN  )
		else:
			self.drdy_pin	= Pin( "D4", Pin.IN  )
		'''
		self.drdy_pin	= Pin( "D0", Pin.IN  )
			
		if "MIMXRT101" not in os.uname().machine:
			self.int_pin	= Pin( "D3", Pin.IN  )
		
		self.reset_pin.value( 1 )
		self.syn_pin.value( 1 )

		self.reset( hardware_reset = True )
		
		self.coeff_microvolt	= [ 0 ] * 16
		self.channel_delay		= [ 0 ] * 16
		self.enabled_ch_list	= []
		
		self.rREG_DICT = {v: k for k, v in self.REG_DICT.items()}
		
		self.drdy_flag	= False
	
	def continuous_read_start( self ):
		self.bit_operation( "SYS_CONFIG0", 0x0010, 0x0010 )
		self.drdy_pin.irq( trigger = Pin.IRQ_RISING, handler = self.drdy_callback )

		self.data	= []

		self.drdy_flag	= False
		self.reg( "CMD_MC" )

	def continuous_read_cb( self, _ ):
		self.data	= self.burst_read()
		
	def drdy_callback( self, p ):
		schedule( self.continuous_read_cb, 0 )

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
			
		raise AFE_Error( "NAFE13388 couldn't get ready. Check power supply or pin conections" )
	
	def open_logical_channel( self, logical_channel, list ):
		"""
		Logical channel configuration

		Parameters
		----------
		list : list
			List of register values for register 0x20, 0x21, 0x22 and 0x23
			
		"""
		self.reg( self.REG_DICT["CMD_CH0"] + logical_channel )

		for r, v in zip( self.ch_cnfg_reg, list ):
			self.reg( r, v )
			
		bit	= 1 << logical_channel		
		_, self.bitmap	= self.bit_operation( "CH_CONFIG4", bit, bit )

		cc0	= list[ 0 ]
		
		if cc0 & 0x0010:
			self.coeff_microvolt[ logical_channel ]	= ((10.0 / (1 << 24)) / self.pga_gain[ (cc0 >> 5) & 0x7 ]) * 1e6
		else:
			self.coeff_microvolt[ logical_channel ]	= (4.0 / (1 << 24)) * 1e6;
		
		base_freq, delay_setting	= self.freq_and_delay( list[ 1 ], list[ 2 ] )
		
		self.channel_delay[ logical_channel ]	= (1 / base_freq) + delay_setting
		self.num_logcal_ch, self.total_delay, self.enabled_ch_list	= self.total_channel_info()

		print( f"base_freq = {base_freq}, delay_setting = {delay_setting}, self.channel_delay[ logical_channel ] = {self.channel_delay[ logical_channel ]}" )

	def freq_and_delay( self, cc1, cc2 ):
		adc_data_rate		= (cc1 >>  3) & 0x001F
		adc_sinc			= (cc1 >>  0) & 0x0007
		ch_delay			= (cc2 >> 10) & 0x003F
		adc_normal_setting	= (cc2 >>  9) & 0x0001
		ch_chop				= (cc2 >>  7) & 0x0001
		
		base_freq			= self.data_rates[ adc_data_rate ]
		delay_setting		= self.delays[ ch_delay ] / 4608000.00

		if (28 < adc_data_rate) or (4 < adc_sinc) or ((adc_data_rate < 12) and adc_sinc):
			raise AFE_Error( "Logical channel setting error: adc_data_rate={adc_data_rate}, adc_sinc={adc_sinc}" )
		
		if not adc_normal_setting:
			base_freq	/= adc_sinc + 1
		
		if ch_chop:
			base_freq	/= 2

		return base_freq, delay_setting
		
	def close_logical_channel( self, logical_channel ):
		bitmap	= 1 << logical_channel		
		_, self.bitmap	= self.bit_operation( "CH_CONFIG4", bitmap, ~bitmap )
		
		self.num_logcal_ch, self.total_delay, self.enabled_ch_list	= self.total_channel_info()
		
	def total_channel_info( self ):
		ch		= 0
		delay	= 0
		list	= []

		for i in range( 16 ):
			if self.bitmap & (0x1 << i):
				ch		+= 1
				delay	+= self.channel_delay[ i ]
				list	+= [ i ]

		return ch, delay, list

	def read_V( self, ch = None ):
		if ch is not None:
			return self.read( ch ) * self.coeff_microvolt[ ch ] * 1e-6
		else:
			return [ v * self.coeff_microvolt[ ch ] * 1e-6 for ch, v in enumerate( self.read() )]
			
	def read( self, ch = None ):
		"""
		Read input value

		Parameters
		----------
		ch : int
			Logical input channel number or None
			
		Returns
		-------
		list of raw measured values if "ch" was not given

		"""
		
		if ch is not None:
			self.bit_operation( "SYS_CONFIG0", 0x0010, 0x0000 )
			
			self.reg( self.REG_DICT["CMD_CH0"] + ch )
			self.reg( "CMD_SS" )
			sleep( self.channel_delay[ ch ] * self.delay_accuracy )
			return self.reg( self.REG_DICT["CH_DATA0"] + ch )
			
		else:
			self.bit_operation( "SYS_CONFIG0", 0x0010, 0x0010 )
	
			values	= []
			self.reg( "CMD_MM" )
			sleep( self.total_delay * self.delay_accuracy )
			
			"""
			for n in self.enabled_ch_list:
				values	+= [ self.reg( self.REG_DICT["CH_DATA0"] + n ) ]
			"""
			values	= self.burst_read()
			
			return values

		
	def die_temp( self ):
		"""
		Die temperature
		
		Returns
		-------
		float : Die temperature in celcius

		"""
		return self.reg( 0x34, signed = True ) / 64

	def reg( self, reg, value = None, signed = False ):
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

		bit_width	= self.reg_bit_width( reg )

		if (value is not None) or (bit_width == 0):
			if bit_width == 24:
				self.write_r24( reg, value )
			else:
				self.write_r16( reg, value )
		else:
			if bit_width == 24:
				return self.read_r24( reg )
			else:
				return self.read_r16( reg, signed )
	
	def reg_bit_width( self, reg ):
		bit_width	= 24

		if (((reg >> 4) & 0xF) < 0x4) or (((reg >> 4) & 0xF) == 0x7):
			bit_width	= 16

		if (((reg >> 4) & 0xF) < 0x2):
			bit_width	= 0

		return bit_width
	
	def bit_operation( self, reg, target_bits, value ):
		"""
		register bit set/clear
	
		Parameters
		----------
		reg : string or int
			Register name or register address/pointer.
		target_bits : int
			select target bits by setting its bit position 1
		value : int
			set/clear value.
			The bits only set/cleared with same position at
			1 in target_bits.
			
		Returns
		-------
		int : register value before modifying
		int : register value after modifying

		"""
		rv	= self.reg( reg )
		wv	= rv
		
		wv	&= ~(target_bits & ~value)
		wv	|=  (target_bits &  value)

		self.reg( reg, wv )
		return rv, wv


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
		regL	= reg      & 0xFF

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
		regL	= reg      & 0xFF

		data	= bytearray( [ regH, regL, 0xFF, 0xFF, 0xFF ] )
		self.__if.write_readinto( data, data )

		data	+= b'\x00'		
		data	= unpack( ">l", data[2:] )[ 0 ] >> 8

		return data
	
	def burst_read( self ):
		reg		 = self.REG_DICT[ "CMD_BURST_DATA" ] << 1
		reg		|= 0x4000
		regH	= reg >> 8 & 0xFF
		regL	= reg      & 0xFF
		
		data	= bytearray( [ regH, regL ] + [ 0xFF, 0xFF, 0xFF ] * self.num_logcal_ch, )
		self.__if.write_readinto( data, data )
	
		rv	= []
	
		for i in range( self.num_logcal_ch ):
			chunk		 = data[ 1 + (3 * i) : 5 + (3 * i) ]
			chunk[0]	 = 0

			rv	+=[ unpack( ">l", chunk )[ 0 ] ]

		return rv

	def dump( self, list ):
		"""
		Register dump

		Parameters
		----------
		list : list
			List of register address/pointer.
		"""
		for k, v in self.reg_dump( list ).items():
			if k:
				if 24 == v[ "width" ]:
					print( f"{k:22} = {v[ 'value' ]:06X}" )
				else:
					print( f"{k:22} = {v[ 'value' ]:04X}" )
	
	def info_logical_channel( self ):
		print( f"info_logical_channel:" )

		print( f"  enabled channels         = {self.num_logcal_ch}" )
		print( f"  enabled channels bitmap  = {self.num_logcal_ch}" )
		print( f"  total_delay              = {self.total_delay}" );

		for i in range( 16 ):
			if self.bitmap & (0x1 << i):
				print( f"  logical channel {i:2} = ", end = "" )
				self.cc_dump( i )

	def cc_dump( self, logical_channel ):
		"""
		Channel configuration register dump
		"""
		self.reg( self.REG_DICT["CMD_CH0"] + logical_channel )

		for k, v in self.reg_dump( self.ch_cnfg_reg ).items():
			print( f"   {k}: 0x{v[ 'value' ]:04X}", end = "" )
		
		print( "" )

		
	def reg_dump( self, list ):
		"""
		Register dump

		Parameters
		----------
		list : list
			List of register address/pointer.
		"""
		
		data	= dict()
		
		for r in list:
			if r is None:
				reg_name	= None
			else:
				reg_addr	= self.REG_DICT[  r ] if type( r ) != int else r
				reg_name	= self.rREG_DICT[ r ] if type( r ) == int else r
				value		= self.reg( reg_addr )
				width		= self.reg_bit_width( reg_addr )
	
			data[ reg_name ]	= { "value": value, "width": width }
		
		return data

	def blink_leds( self ):
		pattern	= (0x8000, 0x0040, 0x0100, 0x0080, 0x0200, 0x0400, 0x0800, 0x1000,
			0x2000, 0x4000, 0x2000, 0x1000, 0x0800, 0x0400, 0x0200, 0x0080,
			0x0100, 0x0040 )
			
		self.reg( "GPIO_CONFIG0", 0xFFC0 );
		self.reg( "GPIO_CONFIG1", 0xFFC0 );
		self.reg( "GPIO_CONFIG2", 0x0000 );

		for n in range( 2 ):
			for v in pattern:
				self.reg( "GPO_DATA", v )
				sleep_ms( 20 )

		pattern2	= pattern[ :10 ]
		pv			= 0;

		for n in range( 4 ):
			for v in pattern2:
				pv	= pv & ~v if (n % 2) else pv | v
				self.reg( "GPO_DATA", pv )
				sleep_ms( 20 )


if __name__ == "__main__":
	main()
