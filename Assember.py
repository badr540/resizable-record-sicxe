import re
import instfile

class Entry:
    def __init__(self, string, token, attribute):
        self.string = string
        self.token = token
        self.att = attribute


symtable = []

# print(symtable[12].string + ' ' + str(symtable[12].token) + ' ' + str(symtable[12].att))

def lookup(s):
    for i in range(0,symtable.__len__()):
        if s == symtable[i].string:
            return i
    return -1

def insert(s, t, a):
    symtable.append(Entry(s,t,a))
    return symtable.__len__()-1

def init():
    for i in range(0,instfile.inst.__len__()):
        insert(instfile.inst[i], instfile.token[i], instfile.opcode[i])
    for i in range(0,instfile.directives.__len__()):
        insert(instfile.directives[i], instfile.dirtoken[i], instfile.dircode[i])

file = open('input.sic', 'r')
filecontent = []
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 2
locctr = 0
lookahead = ''
startLine = True
inst = 0
objCode = True
format = 0
BASE = 0
modRec = []
maxcurrRecSize= 30
recSizes = []
currentcurrRecSize= 30
recSizeIdx = 0

Xbit4set = 0x800000
Bbit4set = 0x400000
Pbit4set = 0x200000
Ebit4set = 0x100000
Nbit4set = 0x2000000
Ibit4set = 0x1000000

Xbit3set = 0x8000
Bbit3set = 0x4000
Pbit3set = 0x2000
Ebit3set = 0x1000
Nbit3set = 0x20000
Ibit3set = 0x10000

def is_hex(s):
    if s[0:2].upper() == '0X':
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    else:
        return False

def lexan():
    global filecontent, tokenval, lineno, bufferindex, locctr, startLine

    while True:
        # if filecontent == []:
        if len(filecontent) == bufferindex:
            return 'EOF'
        elif filecontent[bufferindex] == '\n':
            startLine = True
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
            lineno += 1
        else:
            break
    if filecontent[bufferindex].isdigit():
        tokenval = int(filecontent[bufferindex])  # all number are considered as decimals
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif is_hex(filecontent[bufferindex]):
        tokenval = int(filecontent[bufferindex][2:], 16)  # all number starting with 0x are considered as hex
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif filecontent[bufferindex] in ['+', '#', '@',',']:
        c = filecontent[bufferindex]
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return (c)
    else:
        # check if there is a string or hex starting with C'string' or X'hex'
        if (filecontent[bufferindex].upper() == 'C') and (filecontent[bufferindex+1] == '\''):
            bytestring = ''
            bufferindex += 2
            while filecontent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue)  # should we deal with literals?
            tokenval = p
        elif (filecontent[bufferindex] == '\''): # a string can start with C' or only with '
            bytestring = ''
            bufferindex += 1
            while filecontent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue)  # should we deal with literals?
            tokenval = p
        elif (filecontent[bufferindex].upper() == 'X') and (filecontent[bufferindex+1] == '\''):
            bufferindex += 2
            bytestring = filecontent[bufferindex]
            bufferindex += 2
            # if filecontent[bufferindex] != '\'':# should we take into account the missing ' error?

            bytestringvalue = bytestring
            if len(bytestringvalue)%2 == 1:
                bytestringvalue = '0'+ bytestringvalue
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'HEX', bytestringvalue)  # should we deal with literals?
            tokenval = p
        else:
            p=lookup(filecontent[bufferindex].upper())
            if p == -1:
                if startLine == True:
                    p=insert(filecontent[bufferindex].upper(),'ID',locctr) # should we deal with case-sensitive?
                else:
                    p=insert(filecontent[bufferindex].upper(),'ID',-1) #forward reference
            else:
                if (symtable[p].att == -1) and (startLine == True):
                    symtable[p].att = locctr
            tokenval = p
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
        return (symtable[p].token)


def error(s):
    global lineno
    print('line ' + str(lineno) + ': '+s)


def match(token):
    global lookahead
    if lookahead == token:
        lookahead = lexan()
    else:
        error('Syntax error')

#checks if the value is negative if so formats it using one's compliment to fit into the instruction
def format_disp(disp):
    if disp < 0:
        disp = abs(disp)
        disp = 0xFFF - disp
        disp += 1
        return disp
    else:
        return disp

def index():
    global bufferindex, symtable, tokenval, inst
    if lookahead == ',':
        match(',')
        if symtable[tokenval].att != 1:
            error('index regsiter should be X')
        else:
            bitset = Xbit3set if format == 3 else Xbit4set
            inst += bitset
        match('REG')
        return True
    return False

#parser -> header body tail
def parse():  
    global lookahead
    lookahead = lexan()  

    header()
    body()
    tail()
    

#header -> ID START NUM
def header():
    global locctr, startAddress, progSize
    tok = tokenval
    match('ID')
    match('START')
    startAddress = symtable[tok].att = locctr = tokenval
    match('NUM')
    if pass1or2 == 2 and objCode:
        #program can only be 5 halfbytes?
        print('H'+ symtable[tok].string+ ''+ '{:06X} {:06X}'.format(startAddress, progSize))


def rest3():
    global inst

    if lookahead == '#':
        #n = 0 i = 1
        bitset = Ibit3set if format == 3 else Ibit4set
        inst += bitset
        match('#')
        rest4() 
    elif lookahead == '@':
        #n = 1 i = 0 
        bitset = Nbit3set if format == 3 else Nbit4set
        inst += bitset
        match('@')
        rest4()   
    elif lookahead == 'ID':
        #n = 1 i = 1
        bitset = (Ibit3set + Nbit3set) if format == 3 else (Ibit4set + Nbit4set)
        inst += bitset

        if  symtable[tokenval].att - locctr <= 2047 and symtable[tokenval].att - locctr >= -2047:
            inst += Pbit3set 
            inst += format_disp(symtable[tokenval].att - locctr)
        elif symtable[tokenval].att - BASE <= 4095:
            inst += Bbit3set 
            inst += format_disp(symtable[tokenval].att - BASE)
        elif format == 4:
            inst += symtable[tokenval].att
        else:
            error("Syntax error")
        
        match('ID')
        index()
    elif lookahead == 'NUM':
        #n = 1 i = 1
        bitset = (Ibit3set + Nbit3set) if format == 3 else (Ibit4set + Nbit4set)
        inst += bitset

        if tokenval > 4095 and format == 3:
            if tokenval - locctr <= 2047 and tokenval - locctr >= -2047:
                inst += Pbit3set
                inst += format_disp(tokenval - locctr)
            elif tokenval - BASE <= 4095:
                inst += Bbit3set 
                inst += format_disp(tokenval - BASE)
            else:
                error("Syntax error")
        else:
            inst += tokenval

        match('NUM')
        index()

    else:
        error('syntax error')

def rest4():
    global inst

    if lookahead == 'ID':
        if  symtable[tokenval].att - locctr <= 2047 and symtable[tokenval].att - locctr >= -2047:
            inst += Pbit3set 
            inst += format_disp(symtable[tokenval].att - locctr)
        elif symtable[tokenval].att - BASE <= 4095:
            inst += Bbit3set 
            inst += format_disp(symtable[tokenval].att - BASE)
        elif format == 4:
            inst += symtable[tokenval].att
        else:
            error("Syntax error")

        match('ID')
    elif lookahead == 'NUM':
        if tokenval > 4095 and format == 3:
            if tokenval - locctr <= 2047 and tokenval - locctr >= -2047:
                inst += Pbit3set
                inst += format_disp(tokenval - locctr)
            elif tokenval - BASE <= 4095:
                inst += Bbit3set 
                inst += format_disp(tokenval - BASE)
            else:
                error("Syntax error")
        else:
            inst += tokenval


        match('NUM')
    else:
        error('Syntax error')

def rest5():
    global inst
    if lookahead == ',':
        match(',')
        inst += symtable[tokenval].att
        match('REG')
    elif lookahead not in ['ID', 'F1', 'F2', 'F3','+', 'END', 'BASE']:
        error('syntax error')

def stmt():
    global startLine, inst, locctr, format, recSizes, currentRecSize, recSizeIdx

    tok = tokenval

    if symtable[tokenval].string != 'RSUB':
        startLine = False

    if lookahead == 'F1':
        
        
        locctr += 1
        format = 0
        if pass1or2 == 2:
            inst = symtable[tokenval].att
        match('F1')
        
        if pass1or2 == 2:
            if objCode:
                if currentcurrRecSize< 1 or currentcurrRecSize== maxRecSize:
                    print()
                    print('T{:06X} {:02X} {:02X}'.format(locctr-1,maxRecSize,inst), end='')
                    currRecSize= maxcurrRecSize- 1
                else:
                    print('{:02X}'.format(symtable[tokenval].att), end='')
                    currRecSize-= 1
            else:
                print('{:02X}'.format(symtable[tokenval].att))
        else:
            if currRecSize> 1: 
                currentRecSize-= 1
            else: 
                recSizes.insert(currentRecSize)
    elif lookahead == 'F2':
        locctr += 2
        format = 2

        if pass1or2 == 2:
            inst = symtable[tokenval].att << 8
        match('F2')
        inst += symtable[tokenval].att << 4
        match('REG')
        rest5()
        if pass1or2 == 2:
            if objCode:
                if currentcurrRecSize< 2 or currentcurrRecSize== maxRecSize:
                    print()
                    print('T{:06X} {:02X} {:04X}'.format(locctr-2,maxRecSize,inst), end='')
                    currRecSize= maxcurrRecSize- 2
                else:
                    print('{:04X}'.format(inst), end='')
                    currRecSize-= 2
            
            else:
                print('{:04X}'.format(inst))
        else:
            if currRecSize> 2: 
                currentRecSize-= 2
            else: 
                recSizes.insert(currentRecSize)

    elif lookahead == 'F3':
        locctr += 3
        format = 3

        if pass1or2 == 2:
            inst = symtable[tokenval].att << 16

        match('F3')
        if symtable[tok].string != 'RSUB':
            rest3()
        else:
            inst += (Nbit3set + Ibit3set)
        if pass1or2 == 2:
            if objCode:
                if curr < 3 or currRecSize == maxRecSize:
                    print()
                    print('T{:06X} {:02X} {:06X}'.format(locctr-3,maxRecSize,inst), end='')
                    currRecSize= maxcurrRecSize- 3
                elif currRecSize> 3:
                    print('{:06X}'.format(inst), end='')
                    currRecSize-= 3
            else:
                print('{:06X}'.format(inst))
        else:
            if currRecSize> 3: 
                currentRecSize-= 3
            else: 
                recSizes.insert(currentRecSize)

    elif lookahead == '+':
        modRec.append(locctr+1)
        locctr += 4
        format = 4
        match('+')
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 24
        inst += Ebit4set
        match('F3')
        if symtable[tok].string != 'RSUB':
            rest3()
        else:
            inst += (Nbit4set + Ibit4set)
        if pass1or2 == 2:
            if objCode:
                if currRecSize < 4 or currRecSize== maxcurrRecSize:
                    print()
                    print('T{:06X} {:02X} {:08X}'.format(locctr-4,maxRecSize,inst), end='')
                    currRecSize= maxcurrRecSize- 4
                elif currRecSize> 4:
                    print('{:08X}'.format(inst), end='')
                    currRecSize-= 4
            else:
                print('{:08X}'.format(inst))
        else:
            if currRecSize> 4: 
                currentRecSize-= 4
            else: 
                recSizes.insert(currentRecSize)
    else:
         error('syntax error')


        

    

def rest2():
    global locctr,recSizes, currentRecSize, recSizeIdx
    size = int(len(symtable[tokenval].att)/2)
    locctr += size
    if lookahead == 'STRING':

        if pass1or2 == 2:
            if objCode:
                if currRecSize< size or currRecSize== maxRecSize:
                    print()
                    print('T{:06x} {:02X} '.format(locctr-size,maxRecSize) + symtable[tokenval].att, end='')
                    currRecSize= maxcurrRecSize- size
                elif currRecSize> size:
                    print(symtable[tokenval].att, end='')
                    currRecSize-= size
            else:
                print(symtable[tokenval].att)
        else:
            if currRecSize>= size: 
                currentRecSize-= size
            else: 
                recSizes.insert(currentRecSize)

        match('STRING')
    elif lookahead =='HEX':

        if pass1or2 == 2:
            if objCode:
                if currRecSize< size or currRecSize== maxRecSize:
                    print()
                    print('T{:06x} {:02X} '.format(locctr-size,maxRecSize) + symtable[tokenval].att, end='')
                    currRecSize= maxcurrRecSize- size
                elif currRecSize> size:
                    print(''+symtable[tokenval].att, end='')
                    currRecSize-= size
            else:
                print(symtable[tokenval].att)
        else:
            if currRecSize>= size: 
                currentRecSize-= size
            else: 
                recSizes.insert(currentRecSize)

        match('HEX')
    else:
        error('syntax error rest2')
    

def data():
    global locctr,recSizes, currentRecSize, recSizeIdx

    if lookahead == 'WORD':
        locctr += 3
        match('WORD')
        if pass1or2 == 2:
            if objCode:
                if currRecSize< 3 or currRecSize== maxRecSize:
                    print()
                    print('T{:06x} {:02x} {:06x}'.format(locctr-3,maxRecSize,tokenval), end='')
                    currRecSize= maxcurrRecSize- 3
                elif currRecSize> 3:
                    print('{:06x}'.format(tokenval), end='')
                    currRecSize-= 3
            else:
                print('{:06x}'.format(tokenval))
        else:
            if currRecSize>= 3: 
                currentRecSize-= 3
            else: 
                recSizes.insert(currentRecSize)

            
        match('NUM')
    elif lookahead == 'RESW':
        match('RESW')
        locctr += 3 * tokenval
        if pass1or2 == 2:
            if not objCode:
                for i in range(tokenval):
                    print('000000')
        match('NUM')
    elif lookahead == 'RESB':
        match('RESB')
        locctr += tokenval

        if pass1or2 == 2:
            if not objCode:
                for i in range(tokenval):
                    print('00')

        match('NUM')
    elif lookahead == 'BYTE':
        match('BYTE')
        rest2()
    else:
        error('syntax error')
    

def rest1():  

    if lookahead in ['F1', 'F2', 'F3','+']:
        stmt()
        body()
    elif lookahead in ['WORD', 'RESW', 'RESB', 'BYTE']:
        data()
        body()
    else:
        error('syntax error rest1')
    

#body ->  ID REST1 | STMT BODY | epsilon
def body():
    global BASE, startLine

    if lookahead == 'ID':
        match('ID')
        rest1()
    elif lookahead in ['F1', 'F2', 'F3','+']:
        stmt()
        body()
    elif lookahead == 'BASE':
        startLine = False
        match('BASE')
        BASE = symtable[tokenval].att
        match('ID')
        body()
    elif lookahead != 'END':
        error('syntax error')
    

#tail -> END ID 
def tail():
    global startAddress, progSize
    match('END')
    if pass1or2 == 2 and objCode:
        for i in range(modRec.__len__()):
            if objCode:
                print('M{:06x} {:02x}'.format(modRec[i],5))
        print('E{:06X}'.format(symtable[tokenval].att))

    match('ID')
    progSize = locctr - startAddress        
            
    

def main():
    global file, filecontent, locctr, pass1or2, bufferindex, lineno
    init()
    w = file.read()
    filecontent=re.split("([\W])", w)
    i=0
    while True:
        while (filecontent[i] == ' ') or (filecontent[i] == '') or (filecontent[i] == '\t'):
            del filecontent[i]
            if len(filecontent) == i:
                break
        i += 1
        if len(filecontent) <= i:
            break
    if filecontent[len(filecontent)-1] != '\n': #to be sure that the content ends with new line
        filecontent.append('\n')
    for pass1or2 in range(1,3):
        parse()
        bufferindex = 0
        locctr = 0
        lineno = 1

    file.close()


main()