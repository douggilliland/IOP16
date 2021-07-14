--	---------------------------------------------------------------------------------------------------------
-- Front Panel
-- I2C to Front Panel
--	Test code that loops back the pushbuttons to the LEDs
--	
-- http://land-boards.com/blwiki/index.php?title=Front_Panel_For_8_Bit_Computers
-- Small controller for a Front Panel
-- 32 LEDs, 32 pushbuttons
--
--	IOP16 code
--		https://github.com/douggilliland/IOP16/tree/main/IOP16_Code/FP01_LOOP4
--
--	---------------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use  IEEE.STD_LOGIC_ARITH.all;
use  IEEE.STD_LOGIC_UNSIGNED.all;

entity FrontPanel01_test is
	port
	(
		-- Clock and reset
		i_CLOCK_50					: in std_logic := '1';		-- Clock (50 MHz)
		i_n_reset					: in std_logic := '1';		-- Reset from Pushbutton on FPGA card
		-- The key and LED on the FPGA card
		i_key1						: in std_logic := '1';		-- KEY1 on the FPGA card
		o_UsrLed						: out std_logic := '1';		-- USR LED on the FPGA card
		--
--		o_testPts					: out std_logic_vector(5 downto 0);
		-- External I2C connections
		io_I2C_SCL					: inout std_logic := '0';	-- I2C clock to Front Panel card
		io_I2C_SDA					: inout std_logic := '1';	-- I2C data to/from Front Panel card
		i_I2C_INTn					: in std_logic := '1'		-- Interrupt input - active low
	);
	end FrontPanel01_test;

architecture struct of FrontPanel01_test is
	-- 
	signal w_resetClean_n		:	std_logic;								-- De-bounced reset button
	
	-- Pushbutton signals
	signal w_LEDsOut			:	std_logic_vector(31 downto 0);	-- Pushbutton loopback to LEDs
	signal w_PBsRaw			:	std_logic_vector(31 downto 0);	-- Pushbuttons raw input
	signal w_PBLatched		:	std_logic_vector(31 downto 0);	-- Pushbuttons latched input (de-bounced)
	signal w_PBsToggled		:	std_logic_vector(31 downto 0);	-- Pushbuttons toggled input

begin

	w_LEDsOut <= w_PBsToggled;

	-- Loopback values
	debounceReset : entity work.Debouncer
		port map
		(
			i_clk		=> i_CLOCK_50,
			i_PinIn	=> i_n_reset,
			o_PinOut	=> w_resetClean_n
		);
	
	-- -------------------------------------------------------------------------------------------------------
	-- Front Panel starts here
	
	fp01 : work.FrontPanel01
		-- Need to pass down instruction RAM and stack sizes
		generic	map ( 
			INST_ROM_SIZE_IN	=> 512,
			STACK_DEPTH_IN		=> 4
		)
		port map
		(
			-- Clock and reset
			i_CLOCK_50			=> i_CLOCK_50,				-- Clock (50 MHz)
			i_n_reset			=> w_resetClean_n,			-- Reset
			-- 32 outs, 32 ins
			i_FPLEDs				=> w_LEDsOut,				-- Out to LEDs (32)
			o_PBRaw				=> w_PBsRaw,				-- Raw version of the  Pushbuttons (32)
			o_PBLatched			=> w_PBLatched,			-- Latched version of the  Pushbuttons (32)
			o_PBToggled			=> w_PBsToggled,			-- Toggle version of the  Pushbuttons (32)
			-- Key (pushbutton) and LED on FPGA card
			i_key1				=> i_key1,
			o_UsrLed				=> o_UsrLed,
			-- I2C interface
			io_I2C_SCL			=> io_I2C_SCL,				-- I2C clock to Front Panel card
			io_I2C_SDA			=> io_I2C_SDA,				-- I2C data to/from Front Panel card
			i_I2C_INTn			=> i_I2C_INTn				-- Interrupt input - active low
		);

	-- Front Panel ends here
	-- -------------------------------------------------------------------------------------------------------

end;
