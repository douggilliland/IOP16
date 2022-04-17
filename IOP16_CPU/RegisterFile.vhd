-- ---------------------------------------------------------------------------------
-- File: RegisterFile.vhd
-- Register file for IOP-16 CPU
--	8-bit registers
--	4, 8 or 16 registers
--	3 are constants
--		reg8 = 0x00
--		reg9 = 0x01
--		regF = 0xFF

LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
USE ieee.numeric_std.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

ENTITY RegisterFile IS
	generic (
		constant NUM_REGS : integer := 8	-- 4, 8. or 16
	);
  PORT  (
		i_clock		: in std_logic;		-- Clock (50 MHz)
		i_ldRegF		: in std_logic;		-- Load signal
		i_regSel		: in std_logic_vector(3 downto 0);
		i_RegFData	: in std_logic_vector(7 downto 0);
		o_RegFData	: out std_logic_vector(7 downto 0)
	);
END RegisterFile;

ARCHITECTURE beh OF RegisterFile IS

	signal reg0 	: std_logic_vector(7 downto 0) := X"00";
	signal reg1 	: std_logic_vector(7 downto 0) := X"00";
	signal reg2 	: std_logic_vector(7 downto 0) := X"00";
	signal reg3 	: std_logic_vector(7 downto 0) := X"00";
	signal reg4 	: std_logic_vector(7 downto 0) := X"00";
	signal reg5 	: std_logic_vector(7 downto 0) := X"00";
	signal reg6 	: std_logic_vector(7 downto 0) := X"00";
	signal reg7 	: std_logic_vector(7 downto 0) := X"00";
	signal regA 	: std_logic_vector(7 downto 0) := X"00";
	signal regB 	: std_logic_vector(7 downto 0) := X"00";
	signal regC 	: std_logic_vector(7 downto 0) := X"00";
	signal regD 	: std_logic_vector(7 downto 0) := X"00";
	signal regE 	: std_logic_vector(7 downto 0) := X"00";
	
BEGIN

	-- Register stores
	REGFILE4 : if (NUM_REGS = 4) generate
	begin
		RegisterFile : PROCESS (i_clock)			-- Sensitivity list
			BEGIN
				IF rising_edge(i_clock) THEN		-- On clocks
					if    ((i_ldRegF = '1') and (i_regSel = x"0")) then
						reg0 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"1")) then
						reg1 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"2")) then
						reg2 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"3")) then
						reg3 <= i_RegFData;
					END IF;
				END IF;
			END PROCESS;

	-- Register Read Multiplexer
	o_RegFData <=	reg0	when i_regSel = x"0" else
						reg1	when i_regSel = x"1" else
						reg2	when i_regSel = x"2" else
						reg3	when i_regSel = x"3" else
						x"00"	when i_regSel = x"8" else
						x"01"	when i_regSel = x"9" else
						x"FF"	when i_regSel = x"F" else
						x"00";
		
	end generate REGFILE4;
	
	-- Register stores
	REGFILE8 : if (NUM_REGS = 8) generate
	begin
		RegisterFile : PROCESS (i_clock)			-- Sensitivity list
			BEGIN
				IF rising_edge(i_clock) THEN		-- On clocks
					if    ((i_ldRegF = '1') and (i_regSel = x"0")) then
						reg0 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"1")) then
						reg1 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"2")) then
						reg2 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"3")) then
						reg3 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"4")) then
						reg4 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"5")) then
						reg5 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"6")) then
						reg6 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"7")) then
						reg7 <= i_RegFData;
					END IF;
				END IF;
			END PROCESS;

	-- Register Read Multiplexer
	o_RegFData <=	reg0	when i_regSel = x"0" else
						reg1	when i_regSel = x"1" else
						reg2	when i_regSel = x"2" else
						reg3	when i_regSel = x"3" else
						reg4	when i_regSel = x"4" else
						reg5	when i_regSel = x"5" else
						reg6	when i_regSel = x"6" else
						reg7	when i_regSel = x"7" else
						x"00"	when i_regSel = x"8" else
						x"01"	when i_regSel = x"9" else
						x"FF"	when i_regSel = x"F" else
						x"00";
		
	end generate REGFILE8;
	
	-- Register stores
	REGFILE16 : if (NUM_REGS = 16) generate
	begin
		RegisterFile : PROCESS (i_clock)			-- Sensitivity list
			BEGIN
				IF rising_edge(i_clock) THEN		-- On clocks
					if    ((i_ldRegF = '1') and (i_regSel = x"0")) then
						reg0 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"1")) then
						reg1 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"2")) then
						reg2 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"3")) then
						reg3 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"4")) then
						reg4 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"5")) then
						reg5 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"6")) then
						reg6 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"7")) then
						reg7 <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"A")) then
						regA <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"B")) then
						regB <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"C")) then
						regC <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"D")) then
						regD <= i_RegFData;
					elsif ((i_ldRegF = '1') and (i_regSel = x"E")) then
						regE <= i_RegFData;
					END IF;
				END IF;
			END PROCESS;

	-- Register Read Multiplexer
	o_RegFData <=	reg0	when i_regSel = x"0" else
						reg1	when i_regSel = x"1" else
						reg2	when i_regSel = x"2" else
						reg3	when i_regSel = x"3" else
						reg4	when i_regSel = x"4" else
						reg5	when i_regSel = x"5" else
						reg6	when i_regSel = x"6" else
						reg7	when i_regSel = x"7" else
						x"00"	when i_regSel = x"8" else
						x"01"	when i_regSel = x"9" else
						regA	when i_regSel = x"A" else
						regB	when i_regSel = x"B" else
						regB	when i_regSel = x"C" else
						regD	when i_regSel = x"D" else
						regE	when i_regSel = x"E" else
						x"FF"	when i_regSel = x"F";
		
	end generate REGFILE16;

END beh;

