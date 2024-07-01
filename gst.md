# GST Modules

- `stklen` `<input stack>` : Will put in the stack `iso` the lenght of the stack.
- `execute` `<file path>` : Will execute in a other instance the rud program.
- `include` `<file path>` : Will execute in a other instance the rud program and push all stack items of the new instance in the root instance.
- `inject` `<file path>` : Will inject the lines of the rud program in the root instance.
- `function` `<start/end> <name>` : Will start/end a function (to end, need to de-avoid).
- `call` `<name> <input stack> <output stack>` : Will call a function.
- `case` `<'>'/'<'/'?='> <instruction>` : Will execute the instruction if the condition is true.
