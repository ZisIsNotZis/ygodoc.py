#!/bin/env python3
from re import split, findall
from json import dump
sublime = []
for obj in 'card', 'group', 'effect', 'duel', 'debug':
    for s in split(f'int32_t\\s+scriptlib::{obj}_', open(f'ocgcore/lib{obj}.cpp').read())[1:]:
        f = s.partition('(')[0].title().replace('_', '')
        if f != 'Duel.ConfirmCards' and f.endswith('Cards'):
            f = f[:-1]
        n = 0
        params = {}
        names = {}
        ret = set()
        for nam, clz, g, chk, i in findall(r'(?:([a-zA-Z_][a-zA-Z0-9_]*)?(?:\[[^\]]*\])?\s*=)?\s*(?:\(\s*)*\*?\s*(?:\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\*\s*)*\))?\s*(check_param_count|check_filter|check_param|get_operation_value|interpreter::[a-z0-9_]+|lua_to[a-z]+|lua_push[a-z]+|lua_is[a-z]+)\s*\(\s*(?:L|pcard|\*cit)\s*,(?:\s*([a-zA-Z_]+)\s*,)?(.*)', s):
            i = [int(i)for i in findall(r'\b(.*?)\b', i)if i.isdecimal()]
            if nam:
                names[i[0]-1 if i else n-1] = nam
            match g:
                case 'check_param_count':
                    if i:
                        n = min(n, i[0]) or i[0]
                case 'lua_isnil':
                    params.setdefault(i[0]-1 if i else n-1, set()).add('nil')
                case 'lua_isinteger' | 'lua_isnumber' | 'lua_tointeger' | 'lua_tonumber':
                    params.setdefault(i[0]-1 if i else n-1, set()).add('int')
                case 'lua_isboolean' | 'lua_toboolean':
                    params.setdefault(i[0]-1 if i else n-1, set()).add('bool')
                case 'lua_isstring' | 'lua_tostring':
                    params.setdefault(i[0]-1 if i else n-1, set()).add('str')
                case 'lua_isfunction' | 'interpreter::get_function_handle' | 'check_filter' | 'get_operation_value':
                    params.setdefault(i[0]-1 if i else n-1, set()).add('fn')
                case 'lua_isuserdata':
                    params.setdefault(i[0]-1 if i else n-1, set()).add('obj')
                case 'lua_touserdata':
                    assert clz in ('card', 'group', 'effect'), clz
                    params.setdefault(i[0]-1 if i else n-1, set()).add(clz)
                case 'check_param':
                    match chk:
                        case 'PARAM_TYPE_INT' | 'PARAM_TYPE_FLOAT':
                            params.setdefault(i[0]-1 if i else n-1, set()).add('int')
                        case 'PARAM_TYPE_BOOLEAN':
                            params.setdefault(i[0]-1 if i else n-1, set()).add('bool')
                        case 'PARAM_TYPE_STRING':
                            params.setdefault(i[0]-1 if i else n-1, set()).add('str')
                        case 'PARAM_TYPE_FUNCTION':
                            params.setdefault(i[0]-1 if i else n-1, set()).add('fn')
                        case 'PARAM_TYPE_CARD':
                            params.setdefault(i[0]-1 if i else n-1, set()).add('card')
                        case 'PARAM_TYPE_GROUP':
                            params.setdefault(i[0]-1 if i else n-1, set()).add('group')
                        case 'PARAM_TYPE_EFFECT':
                            params.setdefault(i[0]-1 if i else n-1, set()).add('effect')
                        case _:
                            assert False, chk
                case 'lua_pushinteger':
                    ret.add('int')
                case 'lua_pushboolean':
                    ret.add('bool')
                case 'lua_pushstring':
                    ret.add('str')
                case 'interpreter::function2value':
                    ret.add('fn')
                case 'interpreter::card2value':
                    ret.add('group')
                case 'interpreter::group2value':
                    ret.add('card')
                case 'interpreter::effect2value':
                    ret.add('effect')
                case 'lua_pushvalue':
                    ret.add('val')
                case _:
                    assert False, g
        params = [('|'.join(params.get(i, '')) or 'any', names.get(i, 'o'))for i in range(max(names | params | {-1: None})+1)]
        ret = '|'.join(ret) or 'nil'
        snippet = (obj.title()+'.'if obj in'dueldebug'else'')+f+'('+', '.join(f'${{{i}:{j}}}'for i, (_, j) in enumerate(params[(0 if obj in'dueldebug'else 1):n], 1))+')'
        signature = ret+' '+obj.title()+'.'+f+'('+', '.join(map(' '.join, params[:n]))+('/*'+''.join(f', {i} {j}' for i, j in params[n:])+'*/' if n < len(params)else '')+')'
        sublime.append({
            'trigger': (obj.title()+'.'if obj in'dueldebug'else'')+f,
            'contents': snippet,
            'description': signature,
            'details': signature
        })
        print(signature)
dump({'scope': 'source.lua', 'completions': sublime}, open('ygo.sublime-completions', 'w'), indent=2)
