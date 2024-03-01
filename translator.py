import sys
from isa import Prefix, Instruction, Opcode

regs = {
        "rax": [0, None],
        "rbx": [0, None],
        "rdx": [0, None],
        "rcx": [0, None],
        "r7": [0, None],
        "r8": [0, None]
    }

func_table = {}

stack = []

code = []

key_words = ["if", "loop", "defun", "defvar",
             "setq", "let", "+", "-", "==", "!=",
             "mod", "div", "*", "read", "print"]


# Класс для представления аргументов и тела функции в таблице функций
class FunctionBody:
    def __init__(self, args: list[str] | None, body: list[str] | str | int) -> None:
        self.args = args
        self.body = body

    def __str__(self):
        return f"FunctionBody({self.args}, {self.body})"

    def get_args(self) -> list[str] | None:
        return self.args

    def get_body(self) -> list[str] | None:
        return self.body

    def set_args(self, args: list[str]) -> None:
        self.args = args

    def set_body(self, body: list[str]) -> None:
        self.body = body


def clear_register(register: str, registers: dict) -> None:
    registers[register][0] = 0
    registers[register][1] = None


def find_unused_register(registers: dict) -> str | None:
    for register in registers:
        if registers[register][0] == 0 and registers[register][1] is None:
            return register
    return None


def set_register(register: str, operation: list, registers: dict) -> None:
    registers[register][0] += 1
    registers[register][1] = operation


def push_to_stack(register: str) -> None:
    global stack, registers_state
    stack.append(registers_state[register])
    clear_register(register)


def pop_from_stack(register: str) -> None:
    global stack, registers_state
    registers_state[register] = stack.pop(registers_state[register])



def find_var_in_stack(name: str) -> bool:
    global stack
    for item in stack:
        if item[0] == name:
            return True
    return False


def is_leaf(expression: list) -> bool:
    for item in expression:
        if isinstance(item, list):
            return False
    return True


def lists_count(expression: list) -> int:
    counter = 0
    for item in expression:
        if isinstance(item, list):
            counter += 1
    return counter


def count_unused_registers(registers: dict) -> int:
    counter = 0
    for reg in registers.keys():
        if registers[reg][0] == 0 and registers[reg][1] is None:
            counter += 1
    return counter


def construct_instr_reg(registers: dict, expression: list) -> str:
    reg = find_unused_register(registers)
    set_register(reg, expression, registers)
    return reg


def to_tokens(source: str) -> list[str]:
    return source.strip().replace("\n", "").replace("(", " ( ").replace(")", " ) ").split()


def convert_to_lists(tokens: list) -> list:
    token = tokens.pop(0)
    if token == "(":
        temp = []
        while tokens[0] != ")":
            temp.append(convert_to_lists(tokens))
        tokens.pop(0)
        return temp
    return token


def preprocess(tokens: list) -> list | None:
    global code
    for token in tokens:
        reg = find_unused_register(regs)
        set_register(reg, token, regs)
        code.append(construct_instruction(token, reg))
        clear_register(reg, regs)
    return tokens


# исправить кодогенерацию для условий перехода т.к. на данный момент они представляют из себя просто блок кода CMP!!!!
def construct_instruction(expression: list, reg: str | None) -> list[Instruction]:
    instructions = []

    registers = {
        "rax": [0, None],
        "rbx": [0, None],
        "rdx": [0, None],
        "rcx": [0, None],
        "r7": [0, None],
        "r8": [0, None]
    }
    match expression[0]:
        case "defun":
            assert len(expression) == 4, "Invalid function definition!"
            func_table[expression[1]] = FunctionBody(expression[2], expression[3])
            instructions.append(expression[2])
            if isinstance(expression[3], list):
                for i in range(len(expression[3])):
                    instructions.append(construct_instruction(expression[3][i],
                                                              construct_instr_reg(registers, expression[3][i])))
            else:
                instructions.append(construct_instruction(expression[3], construct_instr_reg(registers, expression[3])))
            instr = Instruction(None, Opcode.RET, expression[1])
            instructions.append(instr)
            return instructions
        case "defvar":
            assert len(expression) == 3, "Invalid global var definition!"
            func_table[expression[1]] = FunctionBody(None, expression[2])
            if isinstance(expression[2], list):
                register = construct_instr_reg(registers, expression[2])
                instructions.append(construct_instruction(expression[len(expression) - 1], register))
                instr = Instruction(None, Opcode.MOV, [expression[1], reg]  )
                instructions.append(instr)
            else:
                register = construct_instr_reg(registers, expression)
                instructions.append(Instruction(None, Opcode.MOV, [register, expression[2]]))
                instr = Instruction(None, Opcode.MOV, [expression[1], reg])
                instructions.append(instr)
            return instructions
        case "let":
            assert len(expression) == 3, "Invalid local var definition!"
            if isinstance(expression[2], list):
                set_register(reg, expression[2], registers)
                instructions.append(construct_instruction(expression[len(expression) - 1], reg))
                instr = Instruction(None, Opcode.PUSH, reg)
                instructions.append(instr)
            else:
                set_register(reg, expression[2], registers)
                instructions.append(Instruction(None, Opcode.MOV, [reg, expression[2]]))
                instr = Instruction(None, Opcode.PUSH, reg)
                instructions.append(instr)
            return instructions
        case "setq":
            assert len(expression) == 3, "Invalid var set expression!"
            if isinstance(expression[2], list):
                register = construct_instr_reg(registers, expression[2])
                instructions.append(construct_instruction(expression[len(expression) - 1], register))
                instr = Instruction(None, Opcode.MOV, [expression[1], reg])
                instructions.append(instr)
            else:
                register = construct_instr_reg(registers, expression)
                instructions.append(Instruction(None, Opcode.MOV, [register, expression[2]]))
                instr = Instruction(None, Opcode.MOV, [expression[1], reg])
                instructions.append(instr)
            return instructions
        case "loop":
            assert len(expression) == 3, "Invalid loop definition!"
            set_register(reg, expression[2], registers)
            counter_reg = find_unused_register(registers)
            set_register(counter_reg, expression[1], registers)
            instructions.append(construct_instruction(expression[1], counter_reg))
            for token in expression[2]:
                if isinstance(token, list):
                    for i in range(len(token)):
                        instructions.append(construct_instruction(token[i], reg))
                else:
                    instructions.append(token)
            instructions.append(Instruction(None, Opcode.JMP, expression[1]))
            return instructions
        case "if":
            assert len(expression) == 4, "Invalid len arguments in if-expression!"
            if isinstance(expression[1], list):
                set_register(reg, expression[1], registers)
                instructions.append(construct_instruction(expression[1], reg))
            instructions.append(Instruction(None, Opcode.JP, expression[2]))
            for i in [2, 3]:
                if isinstance(expression[i], list):
                    instructions.append(construct_instruction(expression[i], reg))
                    instructions.append(Instruction(None, Opcode.JMP, expression))
                else:
                    instructions.append(Instruction(None, Opcode.MOV, [reg, expression[i]]))
                    instructions.append(Instruction(None, Opcode.JMP, expression[i]))
            return instructions
        case "+":
            for i in range(1, len(expression)):
                if i == 1 and not isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(Instruction(None, Opcode.MOV, [reg, expression[i]]))
                elif i == 1 and isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(
                        construct_instruction(expression[i], reg))
                elif isinstance(expression[i], list) and i != 1:
                    instructions.append(construct_instruction(expression[i],
                                                              construct_instr_reg(registers, expression[i])))
            operands = [item for item in registers.keys() if registers[item][0] > 0]
            if reg not in operands:
                operands += [reg]
            for i in range(2, len(expression)):
                if not isinstance(expression[i], list):
                    operands += expression[i]
            instr = Instruction(None, Opcode.ADD, operands)
            instructions.append(instr)
            return instructions
        case "-":
            for i in range(1, len(expression)):
                if i == 1 and not isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(Instruction(None, Opcode.MOV, [reg, expression[i]]))
                elif i == 1 and isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(
                        construct_instruction(expression[i], reg))
                elif isinstance(expression[i], list) and i != 1:
                    instructions.append(construct_instruction(expression[i],
                                                              construct_instr_reg(registers, expression[i])))
            operands = [item for item in registers.keys() if registers[item][0] > 0]
            if reg not in operands:
                operands += [reg]
            for i in range(2, len(expression)):
                if not isinstance(expression[i], list):
                    operands += expression[i]
            instr = Instruction(None, Opcode.SUB, operands)
            instructions.append(instr)
            return instructions
        case "*":
            for i in range(1, len(expression)):
                if i == 1 and not isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(Instruction(None, Opcode.MOV, [reg, expression[i]]))
                elif i == 1 and isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(
                        construct_instruction(expression[i], reg))
                elif isinstance(expression[i], list) and i != 1:
                    instructions.append(construct_instruction(expression[i],
                                                              construct_instr_reg(registers, expression[i])))
            operands = [item for item in registers.keys() if registers[item][0] > 0]
            if reg not in operands:
                operands += [reg]
            for i in range(2, len(expression)):
                if not isinstance(expression[i], list):
                    operands += expression[i]
            instr = Instruction(None, Opcode.MUL, operands)
            instructions.append(instr)
            return instructions
        case "mod":
            assert len(expression) == 3, "Invalid len arguments in mod-expression!"
            for i in [1, 2]:
                if i == 1 and not isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(Instruction(None, Opcode.MOV, [reg, expression[i]]))
                elif i == 1 and isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(
                        construct_instruction(expression[i], reg))
                elif isinstance(expression[i], list) and i != 1:
                    instructions.append(construct_instruction(expression[i],
                                                              construct_instr_reg(registers, expression[i])))
            operands = [item for item in registers.keys() if registers[item][0] > 0]
            if reg not in operands:
                operands += [reg]
            if not isinstance(expression[2], list):
                operands += expression[2]
            instr = Instruction(None, Opcode.MOD, operands)
            instructions.append(instr)
            return instructions
        case "div":
            assert len(expression) == 3, "Invalid len arguments in div-expression!"
            for i in [1, 2]:
                if i == 1 and not isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(Instruction(None, Opcode.MOV, [reg, expression[i]]))
                elif i == 1 and isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(
                        construct_instruction(expression[i], reg))
                elif isinstance(expression[i], list) and i != 1:
                    instructions.append(construct_instruction(expression[i],
                                                              construct_instr_reg(registers, expression[i])))
            operands = [item for item in registers.keys() if registers[item][0] > 0]
            if reg not in operands:
                operands += [reg]
            if not isinstance(expression[2], list):
                operands += expression[2]
            instr = Instruction(None, Opcode.DIV, operands)
            instructions.append(instr)
            return instructions
        case "!=":
            assert len(expression) == 3, "Invalid len arguments in equals-expression!"
            for i in [1, 2]:
                if i == 1 and not isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(Instruction(None, Opcode.MOV, [reg, expression[i]]))
                elif i == 1 and isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(
                        construct_instruction(expression[i], reg))
                elif isinstance(expression[i], list) and i != 1:
                    instructions.append(construct_instruction(expression[i],
                                                              construct_instr_reg(registers, expression[i])))
            operands = [item for item in registers.keys() if registers[item][0] > 0]
            if reg not in operands:
                operands += [reg]
            if not isinstance(expression[2], list):
                operands += expression[2]
            instr = Instruction(None, Opcode.SUB, operands)
            instructions.append(instr)
            return instructions
        case "==":
            assert len(expression) == 3, "Invalid len arguments in equals-expression!"
            for i in [1, 2]:
                if i == 1 and not isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(Instruction(None, Opcode.MOV, [reg, expression[i]]))
                elif i == 1 and isinstance(expression[i], list):
                    set_register(reg, expression[i], registers)
                    instructions.append(
                        construct_instruction(expression[i], reg))
                elif isinstance(expression[i], list) and i != 1:
                    instructions.append(construct_instruction(expression[i],
                                                              construct_instr_reg(registers, expression[i])))
            operands = [item for item in registers.keys() if registers[item][0] > 0]
            if reg not in operands:
                operands += [reg]
            if not isinstance(expression[2], list):
                operands += expression[2]
            instr = Instruction(None, Opcode.SUB, operands)
            instructions.append(instr)
            instructions.append(Instruction(None, Opcode.ADD, [reg, 1]))
            return instructions
        case "read":
            assert len(expression) == 2, "Invalid read arguments!"
            if isinstance(expression[1], list):
                instructions.append(construct_instruction(expression[1]))
            else:
                instructions.append(expression[1])
            instr = Instruction(None, Opcode.LDN, expression[1])
            instructions.append(instr)
            return instructions
        case "print":
            assert len(expression) == 2 or len(expression) == 3, "Invalid print construction!"
            for i in range(1, len(expression)):
                if isinstance(expression[1], list):
                    instructions.append(construct_instruction(expression[1]))
                else:
                    instructions.append(expression[1])
            instr = Instruction(None, Opcode.MVN, expression[1])
            instructions.append(instr)
            return instructions


def compilation(expression: list) -> list:
    pass


def translate(tokens: list[str]) -> list[Instruction]:
    pass


def print_code(cod: list) -> None:
    for i in cod:
        if isinstance(i, Instruction):
            i.print_instruction()
        elif isinstance(i, list):
            print_code(i)
        else:
            print(i)


def main():
    file = open("example/prob1.crisp", "r")
    parse = file.read()
    tokens = to_tokens(parse)
    converted = convert_to_lists(tokens)
    print(converted)
    converted = preprocess(converted)
    print(converted)
    for key in func_table.keys():
        print(key, func_table[key])
    print_code(code)


if __name__ == "__main__":
    main()
