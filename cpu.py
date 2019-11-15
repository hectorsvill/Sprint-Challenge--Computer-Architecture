"""CPU functionality."""

#https://github.com/hectorsvill/Computer-Architecture/blob/master/LS8-spec.md

import sys
#opcodes
LDI = 0X82 # 130
PRN = 0X47  # 71
HLT = 0X01 # 1
MUL = 0XA2 # 162 
PUSH = 0X45 # 69
POP = 0X46 #70
CALL = 0X50# 80
RET = 0X11 #17
ADD = 0XA0 # 160
CMP = 0XA7 # 167




SP = 0XF4 # empty stack address

class CPU:
    """Main CPU class."""
    def __init__(self):
        """Construct a new CPU."""
        self.dispatch_table = self.create_dispatch_table() # dispatch table 0(1) # branch table
        self.halted = False # program is running 
        self.ram = [0] * 256 # ram of 256 bytes
        self.reg = [0] * 8 # register
        self.pc = 0 # Program Counter, address of the currently executing instruction
        self.reg_a =  0 #  Memory Address Register, holds the memory address we're reading or writing
        self.reg_b = 0 # Memory Data Register, holds the value to write or the value just read
        self.ir = 0 # Instruction Register, contains a copy of the currently executing instruction
        self.reg[7] = SP # stack pointer - at address F4, if the stack is empty
        self.fl = 0b00000000 # FL bits: 00000LGE
    def create_dispatch_table(self):
        '''
        Create a dispatch table for faster access
        '''
        dispatch_table = {
            LDI: self.ldi,
            PRN: self.prn,
            HLT: self.hlt,
            MUL: self.mul,
            PUSH: self.push,
            POP: self.pop,
            CALL: self.call,
            RET: self.ret,
            ADD: self.add,
            CMP: self.cmpr,

        }
        return dispatch_table
    def load(self):
        """Load a program into memory."""
        if len(sys.argv) != 2:
            print("usage: cpu.py filename")
            sys.exit()
        else:
            address = 0
            program_name = sys.argv[1]
            with open(program_name) as f:
                for line in f:
                    line = line.split("#")[0]
                    line = line.strip()
                    if line == '':
                        continue
                    val = int(line, 2)
                    self.ram[address] = val
                    address += 1
    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        #elif op == "SUB": etc
        elif op == "CMP":
            if self.reg[reg_a] == self.reg[reg_b]:
                self.fl = 0b00000001
            elif self.reg[reg_a] > self.reg[reg_b]:
                self.fl = 0b00000010
            elif self.reg[reg_a] < self.reg[reg_b]:
                self.fl = 0b00000100
        else:
            raise Exception("Unsupported ALU operation")
    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """
        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')
        for i in range(8):
            print(" %02X" % self.reg[i], end='')
        print()
    def ram_read(self, reg_a):
        """
        should accept the address to read and return the value stored there.
        """
        return self.ram[reg_a]
    def raw_write(self, reg_a, reg_b):
        """
        Should accept a value to write, and the address to write it to.
        """
        self.ram[reg_a] = reg_b
    def reg_write(self, reg_a, reg_b):
        '''
        should accept a memmory address and memory data to registor 
        '''
        self.reg[reg_a] = reg_b
    def register(self):
        '''
        Register data in next two memory addresses
        '''
        self.reg_a = self.ram[self.pc + 1]
        self.reg_b = self.ram[self.pc + 2]
    def ldi(self):
        '''
        load "immediate", store a value in a register, or "set this register to this value".
        '''
        self.reg_write(self.reg_a, self.reg_b)
        self.pc += 3
    def prn(self):
        '''
        a pseudo-instruction that prints the numeric value stored in a register.
        '''
        print(self.reg[self.reg_a])
        self.pc += 2
    def mul(self):
        '''
        Multiply the values in two registers together and store the result in registerA. Machine code:
        '''
        result = self.reg[self.reg_a] * self.reg[self.reg_b]
        self.reg_write(self.reg_a, result)
        self.pc += 3
    def hlt(self):
        '''
        halt the CPU and exit the emulator.
        '''
        self.halted = True
    @property
    def sp(self):
        '''
        get stack pointer
        '''
        return self.reg[7]
    def push(self):
        '''
        Push the value in the given register on the stack. Decrement the SP.
        Copy the value in the given register to the address pointed to by SP.
        '''
        self.reg[7] -= 1
        self.ram[self.sp] = self.reg[self.reg_a]
        self.pc += 2
    def pop(self):
        '''
        Pop the value at the top of the stack into the given register. Copy the
        value from the address pointed to by SP to the given register. Increment SP.
        '''
        value = self.ram[self.sp]
        self.reg[7] -= 1
        self.reg[self.reg_a] = value
        self.pc = self.reg[self.ram[self.pc + 1]]
    def call(self):
        '''
        The address of the instruction directly after CALL is pushed onto the stack. This allows us to return to where we left off when the subroutine finishes executing.
        The PC is set to the address stored in the given register. We jump to that location in RAM and execute the first instruction in the subroutine. The PC can move forward or backwards from its current location.
        '''
        return_address = self.pc + 2
        self.reg[7] -= 1
        self.ram[self.sp] = return_address
        self.pc = self.reg[self.reg_a]
    def ret(self):
        '''
        Return from subroutine.
        Pop the value from the top of the stack and store it in the PC
        '''
        self.pc = self.ram[self.sp]
        self.reg[7] += 1
    def add(self):
        self.alu("ADD", self.reg_a, self.reg_b)
        self.pc += 3 
    def cmpr(self):
        '''
        Compare the values in two registers.
        If they are equal, set the Equal E flag to 1, otherwise set it to 0.
        If registerA is less than registerB, set the Less-than L flag to 1, otherwise set it to 0.
        If registerA is greater than registerB, set the Greater-than G flag to 1, otherwise set it to 0.
        '''
        self.alu("CMP",self.reg_a, self.reg_b)
        self.pc += 3
    def run(self):
        '''
        run cpu
        '''
        while not self.halted:
            self.ir = self.ram_read(self.pc)
            self.register()
            # print(self.ir)
            if self.ir in self.dispatch_table:
                self.dispatch_table[self.ir]()
            else:
                raise Exception(f"did not find instruction in dispatch_table ---> {self.ir}")
if __name__ == "__main__":
    cpu = CPU()
    cpu.load()
    cpu.run()