import sys
from isa import Prefix, Instruction, Opcode

registers_state = {
    "rax": [0, None],
    "rbx": [0, None],
    "rdx": [0, None],
    "rcx": [0, None],
    "r7":  [0, None],
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


def clear_register(register: str) -> None:
    global registers_state
    registers_state[register][0] = 0
    registers_state[register][1] = None


def find_unused_register() -> str:
    global registers_state
    for register in registers_state:
        if registers_state[register][0] == 0 and registers_state[register][1] is None:
            return register
    return "rax"


def set_register(register: str, operation: Instruction) -> None:
    global registers_state
    registers_state[register][0] += 1
    registers_state[register][1] = operation


def push_to_stack(register: str) -> None:
    global stack, registers_state
    stack.append(registers_state[register])
    clear_register(register)


def find_var_in_stack(name: str) -> bool:
    global stack
    for item in stack:
        if item[0] == name:
            return True
    return False


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
        code.append(construct_instruction(token))
    return tokens


# исправить кодогенерацию для условий перехода т.к. на данный момент они представляют из себя просто блок кода CMP!!!!
def construct_instruction(expression: list) -> list[Instruction] | list[str]:
    instructions = []
    match expression[0]:
        case "defun":
            assert len(expression) == 4, "Invalid function definition!"
            func_table[expression[1]] = FunctionBody(expression[2], expression[3])
            instructions.append(expression[2])
            if isinstance(expression[3], list):
                for i in range(len(expression[3])):
                    instructions.append(construct_instruction(expression[3][i]))
            else:
                instructions.append(expression[3])
            instr = Instruction(None, Opcode.RET, expression[1])
            instructions.append(instr)
            return instructions
        case "defvar":
            assert len(expression) == 3, "Invalid global var definition!"
            func_table[expression[1]] = FunctionBody(None, expression[2])
            if isinstance(expression[2], list):
                instructions.append(construct_instruction(expression[len(expression) - 1]))
            else:
                instructions.append(expression[2])
            instr = Instruction(None, Opcode.MOV, [expression[1], expression[2]])
            instructions.append(instr)
            return instructions
        case "let":
            assert len(expression) == 3, "Invalid local var definition!"
            if isinstance(expression[2], list):
                instructions.append(construct_instruction(expression[len(expression) - 1]))
            else:
                instructions.append(expression[2])
            instr = Instruction(None, Opcode.PUSH, [expression[1], expression[2]])
            instructions.append(instr)
            return instructions
        case "setq":
            assert len(expression) == 3, "Invalid var set expression!"
            if expression[1] not in func_table:
                func_table[expression[1]] = FunctionBody(None, expression[2])
            if isinstance(expression[2], list):
                instructions.append(construct_instruction(expression[len(expression) - 1]))
            else:
                instructions.append(expression[2])
            instr = Instruction(None, Opcode.MOV, [expression[1], expression[2]])
            instructions.append(instr)
            return instructions
        case "loop":
            assert len(expression) == 3, "Invalid loop definition!"
            instructions.append(construct_instruction(expression[1]))
            for token in expression[2]:
                if isinstance(token, list):
                    for i in range(len(token)):
                        instructions.append(construct_instruction(token[i]))
                else:
                    instructions.append(token)
                instr = Instruction(None, Opcode.JMP, expression[1])
                instructions.append(instr)
            return instructions
        case "if":
            assert len(expression) == 4, "Invalid len arguments in if-expression!"
            if isinstance(expression[1], list):
                instructions.append(construct_instruction(expression[1]))
            instructions.append(Instruction(None, Opcode.JZ, expression[3]))
            for i in [2, 3]:
                if isinstance(expression[i], list):
                    instructions.append(construct_instruction(expression[i]))
            return instructions
        case "+":
            for i in range(1, len(expression)):
                if isinstance(expression[i], list):
                    instructions.append(construct_instruction(expression[i]))
            instr = Instruction(None, Opcode.ADD, expression[1:])
            instructions.append(instr)
            return instructions
        case "-":
            for i in range(1, len(expression)):
                if isinstance(expression[i], list):
                    instructions.append(construct_instruction(expression[i]))
            instr = Instruction(None, Opcode.SUB, expression[1:])
            instructions.append(instr)
            return instructions
        case "*":
            for i in range(1, len(expression)):
                if isinstance(expression[i], list):
                    instructions.append(construct_instruction(expression[i]))
            instr = Instruction(None, Opcode.MUL, expression[1:])
            instructions.append(instr)
            return instructions
        case "mod":
            assert len(expression) == 3, "Invalid len arguments in mod-expression!"
            for i in [1, 2]:
                if isinstance(expression[i], list):
                    instructions.append(construct_instruction(expression[i]))
            instr = Instruction(None, Opcode.MOD, expression[1:])
            instructions.append(instr)
            return instructions
        case "div":
            assert len(expression) == 3, "Invalid len arguments in div-expression!"
            for i in [1, 2]:
                if isinstance(expression[i], list):
                    instructions.append(construct_instruction(expression[i]))
            instr = Instruction(None, Opcode.DIV, [expression[1], expression[2]])
            instructions.append(instr)
            return instructions
        case "!=":
            assert len(expression) == 3, "Invalid len arguments in equals-expression!"
            for i in [1, 2]:
                if isinstance(expression[i], list):
                    instructions.append(construct_instruction(expression[i]))
            instr = Instruction(None, Opcode.CMP, expression[1:])
            instructions.append(instr)
            return instructions
        case "==":
            assert len(expression) == 3, "Invalid len arguments in equals-expression!"
            for i in [1, 2]:
                if isinstance(expression[i], list):
                    instructions.append(construct_instruction(expression[i]))
            instr = Instruction(None, Opcode.CMP, expression[1:])
            instructions.append(instr)
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
    file = open("example/hello_username.crisp", "r")
    parse = file.read()
    tokens = to_tokens(parse)
    converted = convert_to_lists(tokens)
    print(converted)
    converted = preprocess(converted)
    print(converted)
    for key in func_table.keys():
        print(key, func_table[key])
    print(code)



if __name__ == "__main__":
    main()

# (setq result (+ result (if (== (mod limit 3) 0 ) limit 0) (if (== (mod limit 5) 0 ) limit 0)))
