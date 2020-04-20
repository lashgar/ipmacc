import sys
import xml.etree.ElementTree as ET
import os

sys.path.extend(['.', '..', '../pycparser/'])
from pycparser import c_parser, c_ast

def pycparser_getAstTree(statement):
    text='int main(){\n'+statement+';\n}'
    print text
    # create a pycparser
    parser = c_parser.CParser()
    ast = parser.parse(text, filename='<none>')
    # generate the XML tree
    ast.show()
    codeAstXml = open('code_ast.xml','w')
    ast.showXml(codeAstXml)
    codeAstXml.close()
    tree = ET.parse('code_ast.xml')
    os.remove('code_ast.xml')
    root = tree.getroot()
    return root.find(".//FuncDef/Compound")

def is_arithmc_op(opt):
    list=['+', '-', '*', '/', '%']
    try:
        list.index(opt)
        return True
    except:
        return False

def is_compare_op(opt):
    list=['<', '>', '>=', '<=']
    try:
        list.index(opt)
        return True
    except:
        return False

def is_logical_op(opt):
    list=['&&', '||']
    try:
        list.index(opt)
        return True
    except:
        return False

def analyze_forloop_condition(iterator,root):
    if root.tag.strip()=='ID':
        return [False, (True if iterator==root.get('uid').strip() else False), root.get('uid').strip()]
    elif root.tag.strip()=='Constant':
        return [False, False, root.get('uid').split(',')[-1].strip()]
    code=''
    flag=False  # indicator or expression containing iterator
    ambig=False # indicator of ambiguity in loop boundary detection
    if root.tag.strip()=='BinaryOp':
        [am1, cr1, op1]=analyze_forloop_condition(iterator,root[0])
        opt=root.get('uid')
        [am2, cr2, op2]=analyze_forloop_condition(iterator,root[1])
        print '('+str(cr1)+','+op1+')'+' '+opt+' '+'('+str(cr2)+','+op2+')'
        if is_arithmc_op(opt) or (is_logical_op(opt) and ((cr1 and cr2)or(not(cr1) and not(cr2)))):
            # pass arithmetic operators
            code='('+op1+opt+op2+')'
            flag=cr1 or cr2
        elif is_logical_op(opt):
            # put non-effective element
            code='('+(op1 if cr1 else op2)+')'
            flag=cr1 or cr2
        elif is_compare_op(opt) and (cr1 or cr2):
            # loop terminating condition
            code='('+op1+opt+op2+')'
            flag=True
        elif cr1:
            code=op1
            flag=True
        elif cr2:
            code=op2
            flag=True
        ambig = am1 or am2 or (cr1 and cr2)
    else:
        for it in root:
            [am, cr, cd] = analyze_forloop_condition(iterator, it)
            code=code+'('+cd+')'
            flag=flag or cr
            ambig=ambig or am
    return [ambig, flag, code]

def is_pp_op(opt):
    list=['++p', 'p++']
    try:
        list.index(opt)
        return True
    except:
        return False

def is_mm_op(opt):
    list=['--p', 'p--']
    try:
        list.index(opt)
        return True
    except:
        return False

def analyze_forloop_step(iterator, root, dep):
    ambig=0 # counter of the number of appearences of iterator
    flag=False  # indicator of whether the expression has ambiguity or not
    op=''
    code=''
    if root.tag.strip()=='ID':
        code=root.get('uid').strip()
        ambig=(1 if code==iterator else 0)
    elif root.tag.strip()=='Constant':
        code=root.get('uid').split(',')[-1].strip()
    elif root.tag.strip()=='UnaryOp':
        if is_pp_op(root.get('uid').strip()) and root[0].get('uid').strip()==iterator:
            op='+'
            code='1'
        elif is_mm_op(root.get('uid').strip()) and root[0].get('uid').strip()==iterator:
            op='-'
            code='1'
        else:
            # ambiguity
            flag=True
    elif root.tag.strip()=='BinaryOp' and (root[0].get('uid').strip()==iterator or root[1].get('uid').strip()==iterator):
        if root[0].get('uid').strip()==iterator:
            op=root.get('uid')
            [ambig, flag, op1, code] = analyze_forloop_step(iterator, root[1], dep+1)
        elif root[1].get('uid').strip()==iterator:
            op=root.get('uid')
            [ambig, flag, op2, code] = analyze_forloop_step(iterator, root[0], dep+1)
    elif root.tag.strip()=='BinaryOp':
        [ambig1, flag1, op1, code1] = analyze_forloop_step(iterator, root[0], dep+1)
        [ambig2, flag2, op2, code2] = analyze_forloop_step(iterator, root[1], dep+1)
        ambig = ambig + ambig1 + ambig2
        flag = True
        op = op+op1+op2
        code = code+code2+root.get('uid').strip()+code1
    elif root.tag.strip()=='Assignment':
        if root[0].get('uid')==iterator:
            [ambig, flag, op, code] = analyze_forloop_step(iterator, root[1], dep+1)
        else:
            flag=True
    else:
        for it in root:
            [ambig1, flag1, op1, code1] = analyze_forloop_step(iterator, it, dep+1)
            ambig = ambig + ambig1
            flag = flag or flag1
            op = op+op1
            code = code+code1
    return [ambig, flag, op, code] 

def count_loopIter(init, final, notequal, operator, steps):
    # initial value of operator
    # final value of operator (in respect to loop condition)
    # notequal: whether the greater-equal/lower-equal is permitted
    # operator: the operator of loop iterator increment
    # steps: value of steps for each loop iterator increment
    if operator=='*' or operator=='/':
        return 'log(abs('+final+'-'+init+')'+('-1' if notequal else '')+')'+'/log('+steps+')'
    elif operator=='+' or operator=='-':
        return '(abs('+final+'-'+init+')'+('-1' if notequal else '')+')'+'/('+steps+')'

def calc_index(init, final, notequal, operator, steps, index):
    # initial value of operator
    # final value of operator (in respect to loop condition)
    # notequal: whether the greater-equal/lower-equal is permitted
    # operator: the operator of loop iterator increment
    # steps: value of steps for each loop iterator increment
    # index: the index to calculate its ID
    if operator=='*' or operator=='/':
        return init+operator+'('+index+'^'+steps+')'
    elif operator=='+' or operator=='-':
        return init+'+'+'('+operator+index+'*'+steps+')'

#exps = ['i < j',
#        'j<3 && i<10',
#        '(i>4 || j<3) && (i<10)',
#        'i<10+k',
#        'i<(10*3)+8']
#for st in exps:
#    [k, i, j]=analyze_forloop_condition('i'.strip(),pycparser_getAstTree(st))
#    print '=============expression:'+st
#    print '============='+str(i)+' '+j+(' with ambiguity!' if k else '')

#exps = ['i++', 'i=i+1', 'i--', 'i=(i/k+j/2)-4*3', 'i=i/(k+3-2+4)', 'i=2*i/8']
#for st in exps:
#    [a, f, o, c]=analyze_forloop_step('i'.strip(), pycparser_getAstTree(st), 0)
#    print '==============='+str(f)+' op:'+str(o)+' code:'+c+(' with ambiguity!' if a>1 or f else '')

e=['-100', '0', False, '+', '1']
print count_loopIter(e[0],e[1],e[2],e[3],e[4])+" -> "+calc_index(e[0],e[1],e[2],e[3],e[4],'3')
