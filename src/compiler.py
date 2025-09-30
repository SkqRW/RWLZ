# compiler.py
import json
from typing import List, Dict, Tuple, Any

# --------------------------
# Helpers / tipos simples
# --------------------------
AST = Any
Instr = Tuple[str, Any]  # ("OP", arg) or ("OP", arg1, arg2, ...)
FunctionBytecode = Dict[str, Any]  # {'name':str, 'kind':str, 'params':[], 'bytecode':[] , 'locals':set(), 'ret_type':str}
TYPE_MAP = {
    'int': 'int',
    'float': 'float',
    'bool': 'bool',
    'string': 'string'
}
# comparadores que producen bool
COMPARISON_OPS = {'==', '!=', '<', '<=', '>', '>='}


# --------------------------
# 1) Convertir AST -> bytecode (IR lineal simple)
# --------------------------

def infer_expr_type(expr) -> str:
    """Inferencia simple de tipo desde expr AST."""
    kind = expr[0]
    if kind == 'number':
        val = expr[1]
        return 'float' if isinstance(val, float) else 'int'
    if kind == 'string':
        return 'string'
    if kind == 'var':
        # Sin información de symbol table -> dejar como int por defecto
        return 'int'
    if kind == 'prop':
        return 'int'
    if kind == 'binop':
        op = expr[1]
        if op in COMPARISON_OPS or op in {'&&', '||'}:
            return 'bool'
        # si alguno float -> float
        l = infer_expr_type(expr[2])
        r = infer_expr_type(expr[3])
        if l == 'float' or r == 'float':
            return 'float'
        return 'int'
    if kind == 'unop':
        # '!' produce bool, '-' produce numeric
        op = expr[1]
        if op == '!':
            return 'bool'
        return 'int'
    if kind == 'call':
        # no type info -> int por defecto; normal_function podría devolver bool en base a return
        return 'int'
    return 'int'


def infer_function_return_type(block):
    """Buscar 'return' en el bloque y tratar de inferir."""
    _, stmts = block
    for s in stmts:
        if s[0] == 'return':
            return infer_expr_type(s[1])
        if s[0] == 'if' or s[0] == 'if_else':
            # entrar recursivamente
            if s[0] == 'if':
                _, _, b = s
                t = infer_function_return_type(b)
                if t:
                    return t
            else:
                _, _, b0, b1 = s
                t0 = infer_function_return_type(b0)
                t1 = infer_function_return_type(b1)
                if t0 == t1 and t0:
                    return t0
                if t0:
                    return t0
    return None


def expr_to_bytecode(expr: AST, code: List[Instr], locals_set: set):
    """Genera bytecode simple para expresión. Apila resultado (estilo pila)."""
    kind = expr[0]
    if kind == 'number':
        code.append(('PUSH_CONST', expr[1]))
    elif kind == 'string':
        code.append(('PUSH_CONST', expr[1]))
    elif kind == 'var':
        name = expr[1]
        code.append(('LOAD_VAR', name))
        locals_set.add(name)
    elif kind == 'prop':
        # tratar prop(x) como acceso a parámetro/propiedad: emitimos LOAD_VAR x
        name = expr[1]
        code.append(('LOAD_VAR', name))
        locals_set.add(name)
    elif kind == 'binop':
        op = expr[1]
        left = expr[2]
        right = expr[3]
        expr_to_bytecode(left, code, locals_set)
        expr_to_bytecode(right, code, locals_set)
        code.append(('BINOP', op))
    elif kind == 'unop':
        op = expr[1]
        sub = expr[2]
        expr_to_bytecode(sub, code, locals_set)
        code.append(('UNOP', op))
    elif kind == 'call':
        # call simple: evaluar args y CALL name argc
        _, name, args = expr
        for a in args:
            expr_to_bytecode(a, code, locals_set)
        code.append(('CALL', name, len(args)))
    else:
        code.append(('PUSH_CONST', 0))


def block_to_bytecode(block: AST) -> Tuple[List[Instr], set, str]:
    """
    Convierte block AST a bytecode. Retorna (instructions, locals_set, ret_type)
    """
    code: List[Instr] = []
    locals_set = set()
    _, stmts = block
    for st in stmts:
        kind = st[0]
        if kind == 'var_decl':
            # ('var_decl', p.type, p.ID, p.expr)
            _, typ, name, expr = st
            expr_to_bytecode(expr, code, locals_set)
            code.append(('STORE_VAR', name))
            locals_set.add(name)
        elif kind == 'assign':
            _, name, expr = st
            expr_to_bytecode(expr, code, locals_set)
            code.append(('STORE_VAR', name))
            locals_set.add(name)
        elif kind == 'func_call':
            # ('func_call', ('call', ID, args...))
            _, call = st
            # call is ("call", ID, arg_list)
            _, fname, args = call
            for a in args:
                expr_to_bytecode(a, code, locals_set)
            code.append(('CALL', fname, len(args)))
            # call result is ignored (pop)
            code.append(('POP',))
        elif kind == 'if_else':
            # ('if_else', cond, block_then, block_else)
            _, cond, then_b, else_b = st
            expr_to_bytecode(cond, code, locals_set)
            # simple scheme: create labels as indices; we will emit JZ and JUMP with placeholder and fix labels
            code.append(('JZ', 'LBL_ELSE'))  # placeholder
            # then
            then_code, then_loc, _ = block_to_bytecode(then_b)
            code.extend(then_code)
            code.append(('JUMP', 'LBL_END'))
            code.append(('LABEL', 'LBL_ELSE'))
            else_code, else_loc, _ = block_to_bytecode(else_b)
            code.extend(else_code)
            code.append(('LABEL', 'LBL_END'))
            locals_set.update(then_loc); locals_set.update(else_loc)
        elif kind == 'if':
            # ('if', cond, block)
            _, cond, then_b = st
            expr_to_bytecode(cond, code, locals_set)
            code.append(('JZ', 'LBL_END_IF'))
            then_code, then_loc, _ = block_to_bytecode(then_b)
            code.extend(then_code)
            code.append(('LABEL', 'LBL_END_IF'))
            locals_set.update(then_loc)
        elif kind == 'return':
            # ('return', expr)
            _, expr = st
            expr_to_bytecode(expr, code, locals_set)
            code.append(('RETURN',))
        else:
            # otros tipos no manejados: ignorar
            pass
    # inferir tipo de retorno si hay
    ret_type = infer_function_return_type(('_', stmts))
    return code, locals_set, (ret_type or None)


def ast_to_bytecode(ast: AST) -> Tuple[List[FunctionBytecode], Dict[str,str]]:
    """
    ast expected: ("program", metadata, function_list)
    metadata: ("metadata", s0, s1, s2)
    function_list: [("base_function", ID, params, block), ("normal_function", ...), ...]
    """
    _, metadata, functions = ast
    metadata_dict = {
        "name": metadata[1].strip('"'),
        "description": metadata[2].strip('"'),
        "version": metadata[3].strip('"')
    }

    funcs_bc: List[FunctionBytecode] = []
    for fn in functions:
        kind = fn[0]
        name = fn[1]
        params = fn[2] or []
        block = fn[3]
        bytecode, locals_set, inferred_ret = block_to_bytecode(block)
        # infer return type fallback:
        ret_type = inferred_ret
        if not ret_type:
            # si función base -> int por defecto
            ret_type = 'int' if kind == 'base_function' else 'int'
        # construir lista de params (name,type)
        params_list = [(p[1], p[2][1]) for p in params]  # p = ("param", ID, ("type", 'int'))
        funcs_bc.append({
            'name': name,
            'kind': kind,
            'params': params_list,
            'bytecode': bytecode,
            'locals': list(locals_set),
            'ret_type': ret_type
        })
    return funcs_bc, metadata_dict


# --------------------------
# 2) Generar C# desde bytecode
# --------------------------

def cs_type(t: str) -> str:
    return TYPE_MAP.get(t, 'int')


def indent(lines: List[str], n=1) -> List[str]:
    pad = '    ' * n
    return [pad + l for l in lines]


def bytecode_to_csharp(funcs_bc: List[FunctionBytecode], metadata: Dict[str,str], cs_filename: str, json_filename: str):
    # Escribir metadata json
    with open(json_filename, 'w', encoding='utf-8') as jf:
        json.dump(metadata, jf, indent=4, ensure_ascii=False)

    # Cabecera fija
    header = [
        "using BepInEx;",
        "using BepInEx.Logging;",
        "using System.Security.Permissions;",
        "using Fisobs.Core;",
        "",
        "// Allows access to private members",
        "#pragma warning disable CS0618",
        '[assembly: SecurityPermission(SecurityAction.RequestMinimum, SkipVerification = true)]',
        "#pragma warning restore CS0618",
        "",
        f"namespace {metadata['name'].replace(' ', '')}Mod",
        "{"
    ]
    body: List[str] = []
    # Plugin class
    plugin = [
        f'    [BepInPlugin("{metadata["name"]}", "{metadata["description"]}", "{metadata["version"]}"), BepInDependency("io.github.dual.fisobs")]',
        "    sealed class Plugin : BaseUnityPlugin",
        "    {",
        "        public static new ManualLogSource Logger;",
        "        bool IsInit;",
        "",
        "        public void OnEnable()",
        "        {",
        "            Logger = base.Logger;",
        "            On.RainWorld.OnModsInit += OnModsInit;",
        "            RegisterFisobs();",
        "        }",
        "",
        "        private void OnModsInit(On.RainWorld.orig_OnModsInit orig, RainWorld self)",
        "        {",
        "            orig(self);",
        "",
        "            if (IsInit) return;",
        "            IsInit = true;",
        "",
        '            Logger.LogDebug("Hello world!");',
        "",
        f"            Creatures.{metadata['name'].replace(' ', '')}.Main.Init();",
        "        }",
        "",
        "        private void RegisterFisobs()",
        "        {",
        f"            Content.Register(new {metadata['name'].replace(' ', '')}Critob());",
        "        }",
        "    }",
        ""
    ]
    body.extend(plugin)

    # Clase criatura con funciones
    creature = [
        f"    public class {metadata['name'].replace(' ', '')} : Lizard",
        "    {",
        f"        public {metadata['name'].replace(' ', '')}(AbstractCreature abstractCreature, World world) : base(abstractCreature, world)",
        "        {",
        "        }",
        ""
    ]
    # Generar métodos desde bytecode (traducción simplificada: convertimos instrucciones en líneas C#)
    for f in funcs_bc:
        ret_cs = cs_type(f['ret_type'])
        name = f['name']
        params = f['params']
        params_code = ", ".join(f"{cs_type(t)} {n}" for (n, t) in params)
        # si es base_function -> override
        if f['kind'] == 'base_function':
            sig = f"public override {ret_cs} {name}({params_code})"
        else:
            sig = f"public {ret_cs} {name}({params_code})"
        # convertir bytecode a C# (muy directo: cada RETURN espera un valor en la "pila", lo traducimos inline)
        lines = [sig, "        {"]
        # estrategia simple: traducir instrucciones en orden; mantener un stack temporal de nombres si es necesario
        tmp_stack = []
        tmp_counter = 0
        for instr in f['bytecode']:
            op = instr[0]
            if op == 'PUSH_CONST':
                v = instr[1]
                if isinstance(v, str):
                    tmp = f'@"{v.strip("\"")}"' if '"' in v else f'"{v}"'
                else:
                    tmp = repr(v)
                tmp_stack.append(tmp)
            elif op == 'LOAD_VAR':
                nm = instr[1]
                tmp_stack.append(nm)
            elif op == 'STORE_VAR':
                nm = instr[1]
                if tmp_stack:
                    val = tmp_stack.pop()
                    lines.append(f"            {cs_type('int')} {nm} = {val};")
                else:
                    lines.append(f"            // STORE_VAR {nm} (stack empty)")
            elif op == 'BINOP':
                oper = instr[1]
                # pop right and left
                if len(tmp_stack) >= 2:
                    r = tmp_stack.pop()
                    l = tmp_stack.pop()
                    # map logical operators if needed
                    oper_map = oper
                    if oper == '&&': oper_map = '&&'
                    if oper == '||': oper_map = '||'
                    tmp = f"({l} {oper_map} {r})"
                    tmp_stack.append(tmp)
                else:
                    tmp_stack.append('0')
            elif op == 'UNOP':
                oper = instr[1]
                if tmp_stack:
                    a = tmp_stack.pop()
                    if oper == '!':
                        tmp_stack.append(f"(!{a})")
                    elif oper == '-':
                        tmp_stack.append(f"(-{a})")
                    else:
                        tmp_stack.append(f"({oper}{a})")
                else:
                    tmp_stack.append('0')
            elif op == 'CALL':
                fname = instr[1]
                argc = instr[2]
                args = []
                for _ in range(argc):
                    if tmp_stack: args.append(tmp_stack.pop())
                    else: args.append('0')
                args = list(reversed(args))
                call_expr = f"{fname}({', '.join(args)})"
                tmp_stack.append(call_expr)
            elif op == 'POP':
                if tmp_stack:
                    tmp_stack.pop()
            elif op == 'RETURN':
                if tmp_stack:
                    val = tmp_stack.pop()
                    lines.append(f"            return {val};")
                else:
                    lines.append("            return 0;")
            elif op == 'JZ' or op == 'JUMP' or op == 'LABEL':
                # el IR de control fue simplificado; en codegen simple no reproducimos saltos
                # mejor: ya transformamos if/else en bloques en el AST antes; aquí los saltos son no-op
                pass
            else:
                lines.append(f"            // UNHANDLED INSTR {instr}")
        # en caso de que no haya RETURN en el bytecode, añadir un return por defecto
        if not any(l.strip().startswith('return ') for l in lines):
            default_return = '0'
            if ret_cs == 'bool':
                default_return = 'false'
            elif ret_cs == 'float':
                default_return = '0f'
            elif ret_cs == 'string':
                default_return = '""'
            lines.append(f"            return {default_return};")
        lines.append("        }")
        lines.append("")
        creature.extend(lines)
    creature.append("    }")
    body.extend(creature)

    footer = ["}"]
    # armar archivo
    with open(cs_filename, 'w', encoding='utf-8') as csf:
        for l in header:
            csf.write(l + "\n")
        csf.write("\n")
        for l in body:
            csf.write(l + "\n")
        for l in footer:
            csf.write(l + "\n")

    print(f"Wrote {cs_filename} and {json_filename}")


# --------------------------
# Ejemplo de uso con tu AST
# --------------------------
if __name__ == "__main__":
    # Construimos el AST de ejemplo (como el que mostraste)
    ast_example = (
        "program",
        ("metadata", '"RainLizard"', '"Lizard Mod"', '"1.0"'),
        [
            # base function Move(int speed, float power) { int steps = 10; if (steps > 5) { return prop(speed); } else { return 0; } }
            ("base_function", "Move",
             [("param", "speed", ("type", "int")), ("param", "power", ("type", "float"))],
             ("block", [
                 ("var_decl", ("type", "int"), "steps", ("number", 10)),
                 ("if_else",
                  ("binop", ">", ("var", "steps"), ("number", 5)),
                  ("block", [("return", ("prop", "speed"))]),
                  ("block", [("return", ("number", 0))])
                  )
             ])
             ),
            # normal function Roar(int volume) { return volume == 2; }
            ("normal_function", "Roar",
             [("param", "volume", ("type", "int"))],
             ("block", [
                 ("return", ("binop", "==", ("var", "volume"), ("number", 2)))
             ])
             )
        ]
    )

    funcs_bc, metadata = ast_to_bytecode(ast_example)
    # opcional: imprimir bytecode
    print("=== BYTECODE ===")
    for f in funcs_bc:
        print(f"Function: {f['name']} kind={f['kind']} ret={f['ret_type']}")
        for instr in f['bytecode']:
            print("  ", instr)
        print("  locals:", f['locals'])
        print()

    # generar archivos
    bytecode_to_csharp(funcs_bc, metadata, cs_filename="RainLizard.cs", json_filename="RainLizard.json")
