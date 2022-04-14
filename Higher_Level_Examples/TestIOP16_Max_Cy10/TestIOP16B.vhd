--	---------------------------------------------------------------------------------------------------------
-- Maximal IOP16 CPU Example Code
--		Run software that reads the pushbutton and writes to LED on the FPGA card.
--		https://github.com/douggilliland/IOP16/tree/main/IOP16_Code/testLED
--		Runs on RETRO-EP4CE15
--	
-- IOP16 CPU
--		Custom 16 bit I/O Processor
--		Test Intruction set (enough for basic I/O)
--		4 Clocks per instruction at 50 MHz = 12.5 MIPS
--		Uses 174 ALMs, 109 are in the IOP16
--		Uses 1 M9K SRAM blocks
--
-- IOP16 MEMORY mAP
--		0X00 			- KEY1 Pushbutton (R)
--		0X00			- User LED (R/W)
--		0X01			- User Key (R)
--		0x04-0x07 	- Timer Unit
--		0X08 			- UART (c/S) (r/w)
--		0X09 			- UART (Data) (r/w)
--		0X0A 			- DISPLAY (c/S) (w)
--		0X0B 			- DISPLAY (Data) (w)
--		0X0C			- KBD (c/S) (r)
--		0X0D			- KBD (Data) (r) 
--		0x0E			- Load Constants ROM address (W)
--		0x0E			- Read Constants value (R)
--		
--	---------------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use  IEEE.STD_LOGIC_ARITH.all;
use  IEEE.STD_LOGIC_UNSIGNED.all;

entity TestIOP16B is
	port
	(
		-- Clock and Reset
		i_clk							: in std_logic := '1';		-- Clock (50 MHz)
		i_n_reset					: in std_logic := '1';		-- SW2 on the FPGA card
		-- The key and LED on the FPGA card 
		i_key1						: in std_logic := '1';		-- SW1 on the FPGA card
		
		-- UART
		rxd1			: in std_logic := '1';		-- Hardware Handshake needed
		txd1			: out std_logic;
		cts1			: in std_logic := '1';
		rts1			: out std_logic;
		serSelect	: in std_logic := '1';		-- Jumper with pullup in FPGA for selecting serial between ACIA (installed) and VDU (removed)
		
		-- VGA
		videoR0		: out std_logic := '1';
		videoG0		: out std_logic := '1';
		videoB0		: out std_logic := '1';
		videoR1		: out std_logic := '1';
		videoG1		: out std_logic := '1';
		videoB1		: out std_logic := '1';
		hSync			: out std_logic := '1';
		vSync			: out std_logic := '1';

		-- PS/2 
		ps2Clk		: inout std_logic;
		ps2Data		: inout std_logic;
		
		-- IO_PIN		: out std_logic_vector(48 downto 3);
		
		-- -- External SRAM not used but making sure that it's not active
		sramData		: inout std_logic_vector(7 downto 0);
		sramAddress	: out std_logic_vector(19 downto 0);
		n_sRamWE		: out std_logic := '1';
		n_sRamCS		: out std_logic := '1';
		n_sRamOE		: out std_logic := '1';
		
		-- sD RAM not used but making sure that it's not active
		n_sdRamCas	: out std_logic := '1';		-- CAS on schematic
		n_sdRamRas	: out std_logic := '1';		-- RAS
		n_sdRamWe	: out std_logic := '1';		-- SDWE
		n_sdRamCe	: out std_logic := '1';		-- SD_NCS0
		sdRamClk		: out std_logic := '1';		-- SDCLK0
		sdRamClkEn	: out std_logic := '1';		-- SDCKE0
		sdRamAddr	: out std_logic_vector(14 downto 0) := "000"&x"000";
		sdRamData	: in std_logic_vector(15 downto 0);
		
		-- -- SD Card not used but making sure that it's not active
		sdCS			: out std_logic := '1';
		sdMOSI		: out std_logic := '1';
		sdMISO		: in std_logic := '1';
		sdSCLK		: out std_logic := '1';
		-- -- driveLED		: out std_logic :='1'		-- D5 LED
		o_UsrLed						: out std_logic := '1'		-- USR LED on the FPGA card
	);
	end TestIOP16B;

architecture struct of TestIOP16B is
	-- 
	signal w_resetClean_n		:	std_logic;					-- De-bounced reset button
	
	--  IOP16 Peripheral bus
	signal w_periphAdr			:	std_logic_vector(7 downto 0);
	signal w_periphIn				:	std_logic_vector(7 downto 0);
	signal w_periphOut			:	std_logic_vector(7 downto 0);
	signal w_periphWr				:	std_logic;
	signal w_periphRd				:	std_logic;

-- Decodes/Strobes
	signal w_wrLED					:	std_logic;		-- Write strobe - LED
	signal w_keyBuff				:	std_logic;
	signal w_timerAdr				:	std_logic;
	signal w_wrUart				:	std_logic;
	signal w_rdUart				:	std_logic;
	signal W_VDUWr					:	std_logic;
	signal W_VDURd 				:	std_logic;
	signal w_kbcs					:	std_logic;
	signal w_ldConAdr				:	std_logic;
	signal w_rdConAdr				:	std_logic;

-- Interfaces
	signal w_timerOut				:	std_logic_vector(7 downto 0);
	signal w_UartDataOut			:	std_logic_vector(7 downto 0);
	signal w_VDUDataOut			:	std_logic_vector(7 downto 0);
	signal w_KbdData				:	std_logic_vector(7 downto 0);
	signal w_ConstsData			:	std_logic_vector(7 downto 0);

-- Serial clock enable
	signal W_serialEn      		: std_logic;		-- 16x baud rate clock	

	signal W_LED	      		: std_logic;		-- 
	
	-- Signal Tap Logic Analyzer signals
--	attribute syn_keep	: boolean;
--	attribute syn_keep of w_periphIn			: signal is true;
	
begin

	-- Debounce/sync reset FPGA KEY0 pushbutton to 50 MHz FPGA clock
	debounceReset : entity work.Debouncer
		port map
		(
			i_clk				=> i_clk,
			i_PinIn			=> i_n_reset,
			o_PinOut			=> w_resetClean_n
		);

	-- I/O Processor
	-- Set ROM size in generic INST_SRAM_SIZE_PASS (512W uses 1 of 1K Blocks in EP4CE15 FPGA)
	-- Set stack size in STACK_DEPTH generic
	IOP16: ENTITY work.cpu_001
	-- Need to pass down instruction RAM and stack sizes
		generic map 	( 
			INST_ROM_SIZE_PASS	=> 512,	-- Small code size since program is "simple"
			STACK_DEPTH_PASS		=> 4		-- Single level subroutine (not nested)
		)
		PORT map
		(
			i_clock					=> i_clk,
			i_resetN					=> w_resetClean_n,
			-- Peripheral bus signals
			i_peripDataToCPU		=> w_periphIn,
			o_peripWr				=> w_periphWr,
			o_peripRd				=> w_periphRd,
			o_peripDataFromCPU	=> w_periphOut,
			o_peripAddr				=> w_periphAdr
		);

	-- Peripheral bus read mux
	w_periphIn <=	"0000000"&W_LED		when w_periphAdr = x"00"						else		-- Read-back LED
						"0000000"&i_key1		when w_periphAdr = x"01"						else		-- Read Key pushbutton
						w_timerOut				when w_periphAdr(7 downto 2) = "000001"	else		-- Read timers
						w_UartDataOut			when w_periphAdr(7 downto 1) = "0000100"	else		-- Read UART
						w_VDUDataOut			when w_periphAdr(7 downto 1) = "0000101"	else		-- Read VDU
						w_KbdData				when w_periphAdr(7 downto 1) = "0000110"	else		-- Read PS/2 keyboard
						w_ConstsData			when w_periphAdr = x"0E"						else		-- Read Constants ROM
						x"00";

	-- Strobes/Selects
	w_wrLED		<= '1' when (w_periphAdr=x"00")							and (w_periphWr = '1')	else '0';
	w_timerAdr	<=	'1' when (w_periphAdr(7 downto 2) = "000001")									else '0';
	w_wrUart		<= '1' when (w_periphAdr(7 downto 1) = "0000100")	and (w_periphWr = '1')	else '0';
	w_rdUart		<= '1' when (w_periphAdr(7 downto 1) = "0000100")	and (w_periphRd = '1')	else '0';
	w_VDUWr		<= '1' when (w_periphAdr(7 downto 1) = "0000101")	and (w_periphWr = '1')	else '0';
	w_VDURd		<= '1' when (w_periphAdr(7 downto 1) = "0000101")	and (w_periphRd = '1')	else '0';
	w_kbcs		<= '1' when (w_periphAdr(7 downto 1) = "0000110")	and (w_periphRd = '1')	else '0';
	w_ldConAdr	<= '1' when (w_periphAdr=x"0E")							and (w_periphWr = '1')	else '0';
	w_rdConAdr	<= '1' when (w_periphAdr=x"0E")							and (w_periphRd = '1')	else '0';

	-- Latch up the LED bit
	o_UsrLed <= W_LED;
	latchLEDOut : PROCESS (i_clk,w_wrLED)
	BEGIN
		IF rising_edge(i_clk) THEN
			if w_wrLED = '1' then
				W_LED <= w_periphOut(0);
			END IF;
		END IF;
	END PROCESS;
	
	-- Buffer KEY1
	BUFFER_KEY : PROCESS (i_clk,i_key1)
	BEGIN
		IF rising_edge(i_clk) THEN
			w_keyBuff <= i_key1;						-- Buffer K to avoid metastable inputs
		END IF;
	END PROCESS;
	
	TIMER : entity work.TimerUnit
	port map
	(
		-- Clock and Reset
		i_clk					=> i_clk,
		i_n_reset			=> w_resetClean_n,
		-- The key and LED on the FPGA card 
		i_timerSel			=> w_timerAdr,
		i_writeStrobe		=> w_periphWr,
		i_regSel				=> w_periphAdr(1 downto 0),
		i_dataIn				=> w_periphOut,
		o_dataOut			=> w_timerOut
	);

	-- Baud Rate Generator
	-- These clock enables are asserted for one period of input clk, at 16x the baud rate.
	-- Set baud rate in BAUD_RATE generic
	BAUDRATEGEN	:	ENTITY work.BaudRate6850
		GENERIC map (
		BAUD_RATE	=> 115200
		)
		PORT map (
			i_CLOCK_50	=> i_clk,
			o_serialEn	=> W_serialEn
		);

	-- 6850 style UART
	UART: entity work.bufferedUART
	port map (
		clk     			=> i_clk,
		-- Strobes
		n_wr				=> not w_wrUart,
		n_rd    			=> not w_rdUart,
		-- CPU 
		regSel  			=> w_periphAdr(0),
		dataIn  			=> w_periphOut,
		dataOut 			=> w_UartDataOut,
		-- Clock strobes
		rxClkEn 			=> W_serialEn,
		txClkEn 			=> W_serialEn,
		-- Serial I/F
		rxd     			=> rxd1,
		txd     			=> txd1,
		n_rts   			=> rts1,
		n_cts   			=> cts1
	);
	
	-- Video Display Unit (VDU)
	VDU : entity work.ANSIDisplayVGA
	GENERIC map (
		EXTENDED_CHARSET    => 0,	-- 1 = 256 chars
											-- 0 = 128 chars
		COLOUR_ATTS_ENABLED => 0,	-- 1 = Color for each character
											-- 0 = Color applied to whole display
		SANS_SERIF_FONT     => 1	-- 0 => use conventional CGA font
											-- 1 => use san serif font
	)
	port map (
		clk     => i_clk,
		n_reset => w_resetClean_n,
		-- CPU interface
		n_WR    => not W_VDUWr,
		n_rd    => not W_VDURd,
		regSel  => w_periphAdr(0),
		dataIn  => w_periphOut,
		dataOut => w_VDUDataOut,
		-- VGA video signals
		hSync   => hSync,
		vSync   => vSync,
		videoR0 => videoR0,
		videoR1 => videoR1,
		videoG0 => videoG0,
		videoG1 => videoG1,
		videoB0 => videoB0,
		videoB1 => videoB1
		);

	-- PS/2 keyboard/mapper to ANSI
	KEYBOARD : ENTITY  WORK.Wrap_Keyboard
	port MAP (
		i_CLOCK_50		=> i_clk,
		i_n_reset		=> w_resetClean_n,
		i_kbCS			=> w_kbcs,
		i_RegSel			=> w_periphAdr(0),
		i_rd_Kbd			=> w_kbcs,
		i_ps2_clk		=> ps2Clk,
		i_ps2_data		=> ps2Data,
		o_kbdDat			=> w_KbdData
	);

	-- Constants Unit
	CONST_UNIT : entity work.ConstantsUnit
	port map (	
		i_clock		=> i_clk,
		i_dataIn		=> w_periphOut,
		i_ldStr		=> w_ldConAdr,
		i_rdStr		=> w_rdConAdr,
		o_constData	=> w_ConstsData
	);

end;
