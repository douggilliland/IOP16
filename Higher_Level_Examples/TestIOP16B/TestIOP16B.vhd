--	---------------------------------------------------------------------------------------------------------
-- Simple IOP16B CPU Example Code
--		Run software that reads the pushbutton and writes to LED on the FPGA card.
--		https://github.com/douggilliland/IOP16/tree/main/IOP16_Code/testLED
--		Runs on RETRO-EP4CE15
--	
-- IOP16 CPU
--		Custom 16 bit I/O Processor
--		Minimal Intruction set (enough for basic I/O)
--		8 Clocks per instruction at 50 MHz = 6.25 MIPS
--		Uses 218 LEs, 187 are in the IOP16B
--		Uses 1 M9K SRAM blocks
--
-- IOP16 MEMORY mAP
--		0X00 - KEY1 Pushbutton (R)
--		0X00 - User LED (W)
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
		i_n_reset					: in std_logic := '1';		-- KEY2 on FPGA the card
		-- The key and LED on the FPGA card 
		i_key1						: in std_logic := '1';		-- KEY1 on the FPGA card
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

	signal w_timerOut				:	std_logic_vector(7 downto 0);
	
	-- Decodes/Strobes
	signal w_wrLED					:	std_logic;		-- Write strobe - LED
	signal w_keyBuff				:	std_logic;
	signal w_timerAdr				:	std_logic;
	
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

	timerUnit : entity work.TimerUnit
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

	
	-- I/O Processor
	-- Set ROM size in generic INST_SRAM_SIZE_PASS (512W uses 1 of 1K Blocks in EP4CE15 FPGA)
	-- Set stack size in STACK_DEPTH generic
	IOP16: ENTITY work.cpu_001
	-- Need to pass down instruction RAM and stack sizes
		generic map 	( 
			INST_ROM_SIZE_PASS	=> 512,	-- Small code size since program is "simple"
			STACK_DEPTH_PASS		=> 0		-- Single level subroutine (not nested)
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
	w_periphIn <=	"0000000"&w_keyBuff	when w_periphAdr=x"00"						else
						w_timerOut				when w_periphAdr(7 downto 2) = "000001" else
						x"00";

	-- Strobes/Selects
	w_wrLED		<= '1' when ((w_periphAdr=x"00") 						and (w_periphWr = '1')) else '0';
	w_timerAdr	<=	'1' when (w_periphAdr(7 downto 2) = "000001")									else '0';

	-- Latch up the LED bit
	-- Buffer KEY1
	latchLEDOut : PROCESS (i_clk)
	BEGIN
		IF rising_edge(i_clk) THEN
			if w_wrLED = '1' then
				o_UsrLed <= w_periphOut(0);
			END IF;
			w_keyBuff <= i_key1;						-- Buffer K to avoid metastable inputs
		END IF;
	END PROCESS;
	
end;
