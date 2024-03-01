from enum import Enum


class Registers(Enum):
    rax = "rax"
    rbx = "rbx"
    rcx = "rcx"
    rdx = "rdx"
    rip = "rip"
    rsp = "rsp"
    r7 = "r7"
    r8 = "r8"

    def __str__(self) -> str:
        return self.value


class Opcode(Enum):
    MOV = 'mov', 0x11
    ADD = 'add', 0x12
    SUB = 'sub', 0x13
    MUL = 'mul', 0x14
    DIV = 'div', 0x15
    MOD = 'mod', 0x16

    PUSH = 'push', 0x17
    POP = 'pop', 0x18

    CMP = 'cmp', 0x19
    JMP = 'jmp', 0x1A
    JZ = 'jz', 0x1B
    JNZ = 'jnz', 0x1C
    JN = 'jn', 0x1D
    JP = 'jp', 0x1E

    LDN = 'ldn', 0x1F
    MVN = 'mvn', 0x21

    HLT = 'hlt', 0x22

    CALL = 'call', 0x23
    RET = 'ret', 0x24

    def __str__(self) -> str:
        return str(self.value[0])

    def get_hex(self):
        return self.value[1]


registers: list[Registers] = [Registers.rax, Registers.rbx, Registers.rdx, Registers.rip, Registers.rcx, Registers.rsp]
branch_commands: list[Opcode] = [Opcode.JMP, Opcode.JZ, Opcode.JNZ, Opcode.JN, Opcode.JP]
two_args_commands: list[Opcode] = [Opcode.MOV, Opcode.DIV, Opcode.MOD, Opcode.CMP]
one_operands_commands: list[Opcode] = [Opcode.PUSH, Opcode.POP, Opcode.LDN, Opcode.MVN, Opcode.CALL]
no_args_commands: list[Opcode] = [Opcode.HLT, Opcode.RET]
extended_args_commands: list[Opcode] = [Opcode.ADD, Opcode.SUB, Opcode.MUL]

alu_commands: list[Opcode] = [
    Opcode.ADD,
    Opcode.SUB,
    Opcode.MUL,
    Opcode.DIV,
    Opcode.MOD,
    Opcode.CMP
]


class PrefixType(Enum):
    NOP = 0x0
    REGISTER = 0x1
    MEMORY = 0x2
    VALUE = 0x3
    ONE_OPERAND = 0x4
    NO_OPERAND = 0x5
    STACK = 0x6
    EXPANSION = 0xF

    def __str__(self) -> str:
        return str(self.value)


class Prefix:
    prefix: PrefixType | list[PrefixType]

    def __init__(self, prefix: PrefixType | list[PrefixType]) -> None:
        self.prefix = prefix


class Operand:
    def __init__(self, value: str) -> None:
        pass


class Instruction:
    def __init__(self, prefix: Prefix | None, opcode: Opcode, operands: list[Operand] | None) -> None:
        self.prefix = prefix
        self.opcode = opcode
        self.operands = operands

    def print_instruction(self):
        instruction_array = []
        if self.prefix:
            instruction_array.append(self.prefix)
        instruction_array.append(self.opcode)
        instruction_array.extend(self.operands)
        print(instruction_array)


