from collections import namedtuple
from opcode import *


Number = namedtuple('Number', ['a'])
String = namedtuple('String', ['a'])
Identifier = namedtuple('Identifier', ['a'])

OpUnary = namedtuple('OpUnary', ['op', 'a'])
OpBinary = namedtuple('OpBinary', ['op', 'a', 'b'])

Call = namedtuple('Call', ['i', 'a'])
While = namedtuple('While', ['c', 't'])
IfThen = namedtuple('IfThen', ['c', 't'])
IfThenElse = namedtuple('IfThenElse', ['c', 't', 'f'])


OPCODE_OP_UNARY = (PLUS, MINUS, INV, NOT)
OPCODE_OP_BINARY = (ADD, SUB, MUL, DIV, SHL, SHR, AND, OR, XOR, LAND, LOR, EQ, NE, LT, LE, GT, GE, ASSIGN)


class Block:
    statements = list()

    def parse(self, bytecode, address=0, until=None):
        while True:
            op = bytecode[address]

            if until:
                if op.addr == until:
                    break

            if op.code in (BRK, BRA):
                break

            elif op.code == POP:
                address = op.addr + op.size

            elif op.code in (PUSH, PUSHF):
                statement = Number()
                address = statement.parse(op)
                self.statements.append(statement)

            elif op.code == PUSHS:
                statement = String()
                address = statement.parse(op)
                self.statements.append(statement)

            elif op.code == PUSHI:
                statement = Identifier()
                address = statement.parse(op)
                self.statements.append(statement)

            elif op.code in OPCODE_OP_UNARY:
                statement = Unary()
                address = statement.parse(op, self.statements)
                self.statements.append(statement)

            elif op.code in OPCODE_OP_BINARY:
                statement = Binary()
                address = statement.parse(op, self.statements)
                self.statements.append(statement)

            elif op.code == CALL:
                statement = Call()
                address = statement.parse(op, self.statements, bytecode)
                self.statements.append(statement)

            elif op.code == BF:
                statement = Branch()
                address = statement.parse(op, self.statements, bytecode)
                self.statements.append(statement)

            else:
                raise ValueError("Unhandled opcode")

        return op

    def build(self):
        pass


class Branch:
    expression = None
    blockfalse = None
    blocktrue = None
    islooped = False

    def parse(self, op, block, bytecode):
        self.expression = block.pop()
        self.blocktrue = Block()

        ex = self.blocktrue.parse(bytecode, op.addr + op.size)

        address = op.addr + op.size + op.data

        if ex.code != BRA:
            raise ValueError("Unexpected exit code")

        if (ex.addr + ex.size) != address:
            raise ValueError("Unexpected jump address")

        if ex.data < 0:
            self.islooped = True
            return address

        if ex.data == 0:
            return address

        if ex.data > 0:
            self.blockfalse = Block()
            address_end = ex.addr + ex.size + ex.data
            no = self.blockfalse.parse(bytecode, address, address_end)
            return address_end

        raise ValueError()

    def build(self):
        pass


class Call:
    identifier = None
    arguments = list()

    def parse(self, op, block, bytecode):
        self.identifier = block.pop()

        for address in op.data:
            argument = Block()
            ex = argument.parse(bytecode, address)

            if ex.code != BRK:
                raise ValueError()

            self.arguments.append(argument)

        ex = bytecode[op.addr + op.size]

        if ex.code != BRA:
            raise ValueError()

        return ex.addr + ex.data + ex.size

    def build(self):
        pass


class Unary:
    operation = None
    operand1 = None

    def parse(self, op, block):
        self.operand1 = block.pop()
        self.operation = op.code
        return op.addr + op.size

    def build(self):
        pass


class Binary:
    operation = None
    operand1 = None
    operand2 = None

    def parse(self, op, block):
        self.operand1 = block.pop()
        self.operand2 = block.pop()
        self.operation = op.code
        return op.addr + op.size

    def build(self):
        pass


class Number:
    value = None

    def parse(self, op):
        self.value = op.data
        return op.addr + op.size

    def build(self):
        pass


class String:
    value = None

    def parse(self, op):
        self.value = op.data
        return op.addr + op.size

    def build(self):
        pass


class Identifier:
    value = None

    def parse(self, op):
        self.value = op.data
        return op.addr + op.size

    def build(self):
        pass


def _bf(op, ast, bytecode):
    c = ast.pop()
    bra, t = walk(bytecode, op.addr + op.size)

    if bra.code != BRA:
        raise ValueError("Unexpected exit code in BF")

    if bra.data < 0:
        if (bra.addr + bra.size) != (op.addr + op.size + op.data):
            raise ValueError("Unexpected jump address in BF While")

        n = While(c, t)
        ast.append(n)
        return op.addr + op.size + op.data

    if bra.data == 0:
        if (bra.addr + bra.size) != (op.addr + op.size + op.data):
            raise ValueError("Unexpected jump address in BF IfThen")

        n = IfThen(c, t)
        ast.append(n)
        return op.addr + op.size + op.data

    if bra.data > 0:
        if (bra.addr + bra.size) != (op.addr + op.size + op.data):
            raise ValueError("Unexpected jump address in BF IfThenElse")

        els, f = walk(bytecode, op.addr + op.size + op.data, bra.addr + bra.size + bra.data)

        n = IfThenElse(c, t, f)
        ast.append(n)
        return bra.addr + bra.size + bra.data

    raise ValueError()

def _call(op, ast, bytecode):
    i = ast.pop()
    a = list()

    for jmp in op.data:
        ex, arg = walk(bytecode, jmp)

        if ex.code != BRK:
            raise ValueError()

        a.append(arg)

    n = Call(i, a)
    ast.append(n)

    ex, arg = walk(bytecode, op.addr + op.size)

    if ex.code != BRA or arg:
        raise ValueError()

    return ex.addr + ex.data + ex.size

def _op_unary(op, ast):
    a = ast.pop()
    n = OpUnary(op.code, a)
    ast.append(n)
    return op.addr + op.size

def _op_binary(op, ast):
    a = ast.pop()
    b = ast.pop()
    n = OpBinary(op.code, a, b)
    ast.append(n)
    return op.addr + op.size

def _number(op, ast):
    n = Number(op.data)
    ast.append(n)
    return op.addr + op.size

def _string(op, ast):
    n = String(op.data)
    ast.append(n)
    return op.addr + op.size

def _identifier(op, ast):
    n = Identifier(op.data)
    ast.append(n)
    return op.addr + op.size


def walk(bytecode, address=0, until=None):
    ast = list()

    while True:
        op = bytecode[address]

        if until:
            if op.addr == until:
                break

        if op.code in (PUSH, PUSHF):
            address = _number(op, ast)

        elif op.code == PUSHS:
            address = _string(op, ast)

        elif op.code == PUSHI:
            address = _identifier(op, ast)

        elif op.code in OPCODE_OP_UNARY:
            address = _op_unary(op, ast)

        elif op.code in OPCODE_OP_BINARY:
            address = _op_binary(op, ast)

        elif op.code == CALL:
            address = _call(op, ast, bytecode)

        elif op.code == BF:
            address = _bf(op, ast, bytecode)

        elif op.code == POP:
            address = op.addr + op.size

        elif op.code == BRA:
            break

        elif op.code == BRK:
            break

        else:
            raise ValueError(OPCODE_NAME[op.code])

    return op, ast