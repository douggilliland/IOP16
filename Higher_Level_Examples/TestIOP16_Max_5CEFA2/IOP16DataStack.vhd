-- IOP16DataStack
-- 256 bytes deep FIFO
-- Push a byte by doing a write to Peripheral Address
-- Pull a byte by doing a read from Peripheral Address
-- 1 clock wide write
-- 2 clocks wide read

LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
USE ieee.numeric_std.ALL;
use ieee.std_logic_unsigned.all;

entity IOP16DataStack is
	PORT (
		i_CLOCK_50		: IN std_logic;
		i_n_reset		: IN std_logic;
		i_dataStkDin	: IN std_logic_vector(7 downto 0);
		i_wrDatStk		: IN std_logic;
		i_rdDatStk		: IN std_logic;
		o_dataStkDout	: OUT std_logic_vector(7 downto 0)
	);
end IOP16DataStack;

ARCHITECTURE IOP16DataStack_beh OF IOP16DataStack IS

   signal w_rdStrD1   	: std_logic;
--   signal w_rdStrD2   	: std_logic;

-- Signal Tap Logic Analyzer signals
--	attribute syn_keep of o_serialEn			: signal is true;
	
BEGIN
	LATCH_STK_VAL : PROCESS (i_CLOCK_50,i_rdDatStk)
	BEGIN
		IF rising_edge(i_CLOCK_50) THEN
			w_rdStrD1 <= i_rdDatStk;
--			w_rdStrD2 <= w_rdStrD1;
		end if;
	END PROCESS;
	
DATASTACK : ENTITY work.DataStkFIFO
	PORT MAP
	(
		clock		=> i_CLOCK_50,
		data		=> i_dataStkDin,
		rdreq		=> i_rdDatStk and not w_rdStrD1,
		wrreq		=> i_wrDatStk,
		q			=> o_dataStkDout
	);

	
END IOP16DataStack_beh;
