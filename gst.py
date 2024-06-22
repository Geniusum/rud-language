import rud
import os

script_path = os.path.dirname(os.path.abspath(__file__))

def initgst(self: rud.Interpreter):
    self.gst_vars = {
        "functions": {},
        "function_start_line": None,
        "function_defined": None
    }

def parseFunctionName(self: rud.Interpreter, name:str, already:bool=True, mustexists:bool=False):
    name = str(name.lower().strip())
    chars = [*"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"]
    valid = True
    for char in name:
        if not char in chars:
            valid = False
    if not valid:
        self.error("Gst", "Invalid function name.")
        return
    if name in self.gst_vars["functions"].keys() and already:
        self.error("Gst", "Function name already taken.")
        return
    elif name not in self.gst_vars["functions"].keys() and mustexists:
        self.error("Gst", "The function name don't exists.")
        return
    return name

def stklen(self: rud.Interpreter, args:list[str]):
    stack_name = self.stackInitialized(self.stackExists(args[0]))
    out_stack = self.stackInitialized(self.stackExists("iso"))
    lenght = len(self.getStackList(stack_name))
    self.push(out_stack, lenght)

def execute(self: rud.Interpreter, args:list[str]):
    for arg in args:
        arg = arg.replace("/", "\\")
        if arg.startswith("*") and arg.endswith("*"):
            arg = arg[1:-1]
            path = os.path.join(script_path, "libs", arg)
        else:
            path = arg
        content = open(path).read()
        newintr = rud.Interpreter(content)
        newintr.end_exit = False
        newintr.from_file = os.path.dirname(path).lower() + "/" + os.path.splitext(os.path.basename(path))[0]
        try: newintr.execute(False, False)
        except: pass
        if self.mode == "shell": print()

def include(self: rud.Interpreter, args:list[str]):
    for arg in args:
        arg = arg.replace("/", "\\")
        if arg.startswith("*") and arg.endswith("*"):
            arg = arg[1:-1]
            path = os.path.join(script_path, "libs", arg)
        else:
            path = arg
        content = open(path).read()
        newintr = rud.Interpreter(content)
        newintr.end_exit = False
        newintr.from_file = os.path.dirname(path).lower() + "/" + os.path.splitext(os.path.basename(path))[0]
        try: newintr.execute(False, False)
        except: pass
        for stack_name, stack_dict in newintr.stacks.items():
            self.stacks[stack_name]["locked"] = stack_dict["locked"]
            for item in stack_dict["stack"]:
                self.push(stack_name, item)
        if self.mode == "shell": print()

def inject(self: rud.Interpreter, args:list[str]):
    for arg in args:
        arg = arg.replace("/", "\\")
        if arg.startswith("*") and arg.endswith("*"):
            arg = arg[1:-1]
            path = os.path.join(script_path, "libs", arg)
        else:
            path = arg
        content = open(path).read()
        line_index = self.active_line - 1
        self.lines = self.lines[:line_index + 1] + content.splitlines() + self.lines[line_index + 1:]
        if self.mode == "shell": print()

def function(self: rud.Interpreter, args:list[str]):
    # Syntax : <start/end> <name>
    # The stacks fi (function inputs), fo (function outputs) and fch (function chunk) will be created on the function start and will be deleted at the function end.
    if len(args) == 2:
        stend = args[0].lower()
        name = args[1]
        if stend in ["start", "def", "define"]:
            name = parseFunctionName(self, name, True, False)
            if name != None:
                self.gst_vars["function_start_line"] = self.active_line
                self.avoid = True
                self.gst_vars["function_defined"] = name
        elif stend in ["end", "final", "finalize"]:
            name = parseFunctionName(self, name, False, False)
            if name != None:
                if not name == self.gst_vars["function_defined"]:
                    self.error("Gst", "Function don't match with the actual definition.")
                else:
                    start_line = self.gst_vars["function_start_line"]
                    self.gst_vars["function_defined"] = None
                    lines = self.lines[start_line:self.active_line - 1]
                    lines.reverse()
                    for line_index, line in enumerate(lines):
                        if line.strip().lower() == "avd":
                            lines[line_index] = ";"
                            break
                    lines.reverse()
                    self.gst_vars["functions"][name] = lines
                    self.gst_vars["function_start_line"] = None
    else:
        self.error("Gst", "Invalid function definition/finalization syntax.")

def call(self: rud.Interpreter, args:list[str]):
    # Syntax : <name> <input stack> <output stack>
    if len(args) >= 2:
        name = parseFunctionName(self, args[0], False, True)
        if name != None:
            input_stack = self.stackInitialized(self.stackExists(args[1]))
            if len(args) == 3:
                output_stack = self.stackInitialized(self.stackExists(args[2]))
            else:
                output_stack = self.stackInitialized(self.stackExists("bin"))
            stacks = self.stacks
            stacks["fi"] = {
                "limit": 0,
                "stack": self.getStackList(input_stack),
                "locked": False
            }
            stacks["fo"] = {
                "limit": 0,
                "stack": [],
                "locked": True
            }
            stacks["fch"] = {
                "limit": 16,
                "stack": [],
                "locked": True
            }
            self.stacks = stacks
            lines = self.gst_vars["functions"][name]
            line_index = self.active_line - 1
            for line in lines:
                tokens = line.split()
                if len(tokens):
                    self.execInstruction(tokens)
            if "fi" in self.stacks.keys():
                for item in self.stacks["fo"]["stack"]:
                    self.push(output_stack, item)
                del self.stacks["fi"]
                del self.stacks["fo"]
                del self.stacks["fch"]
    else:
        print(args)
        self.error("Gst", "Invalid function call syntax.")

def case(self: rud.Interpreter, args:list[str]):
    # Syntax : <'>'/'<'/'?='> <instruction ...>
    if len(args) >= 2:
        operators = {
            "upper": ["upper", ">"],
            "lower": ["lower", "<"],
            "equal": ["equal", "?="]
        }

        operator = args[0]
        instruction = args[1:]
        stack_a = self.getLast(self.stackInitialized(self.stackExists("opx")))
        stack_b = self.getLast(self.stackInitialized(self.stackExists("opr")))
        if type(stack_a) == str:
            stack_a = ord(stack_a)
        if type(stack_b) == str:
            stack_b = ord(stack_b)
        if operator in operators["upper"]:
            if stack_a > stack_b:
                self.execInstruction(instruction.split())
        elif operator in operators["lower"]:
            if stack_a < stack_b:
                self.execInstruction(instruction.split())
        elif operator in operators["equal"]:
            if stack_a == stack_b:
                self.execInstruction(instruction.split())
        else:
            self.error("Gst", "Invalid operator.")
    else:
        self.error("Gst", "Invalid function call syntax.")

names = {
    "stklen": stklen,
    "execute": execute,
    "include": include,
    "inject": inject,
    "function": function,
    "call": call,
    "case": case
}