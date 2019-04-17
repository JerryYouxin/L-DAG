import sys
import os
import shutil
from xml.etree import ElementTree as ET
import argparse
import platform
args = None

def parse_MACRO(s, param):
    result = ''
    substr = ''
    analysing = False
    for c in s:
        if c != '$':
            if analysing:
                if c.isalpha() or c == '_':
                    substr += c
                else:
                    analysing = False
                    result += substr + c
                    substr = ''
            else:
                result += c
        else:
            if analysing:
                result += str(param.para[substr[1:]])
                substr = ''
                analysing = False
            else:
                analysing = True
                substr += c
    return result


def parse_expr(expr, param):
    expr_new = parse_MACRO(expr, param)
    return eval(expr_new.replace('\n', '').replace('\r', ''))


def parse_statement(child, param):
    expr = child.findall('expr')
    if len(expr) > 0:
        if len(expr) > 1:
            print('WARNING : there are multiple "expr" in ' + child.tag + ' domain. Only take the first one.')
        val = parse_expr(expr[0].text, param)
    else:
        val = parse_MACRO(child.text, param)
    return val


def parse_parent(domain, beginning, ending):
    edges = {}
    for one in domain:
        pid = one.get('ref')
        if pid in ending:
            ending.remove(pid)
        children = one.findall('child')
        clist = []
        for child in children:
            cid = child.get('ref')
            clist.append(cid)
            if cid in beginning:
                beginning.remove(cid)
        if pid in edges:
            edges[pid].extend(clist)
        else:
            edges[pid] = clist
    return edges


class Parameter:
    def __init__(self):
        self.para = {}

    def add(self, key, val):
        self.para[key] = val

    def parseLine(self, line):
        line.strip()
        sl= line.split('=')
        print("get para = ",sl)
        self.para[sl[0]] = sl[1]

    def general_read(self, fn_para):
        if fn_para=='':
            return
        if not os.path.exists(fn_para):
            print("Error : "+fn_para+" is missing !!!")
            exit(-1)
        f = open(fn_para, 'r', encoding='UTF-8')
        for line in f:
            self.parseLine(line)
        f.close()

    def read(self):
        if not os.path.exists('Parameter.dat'):
            print("Error : Parameter.dat is missing !!!")
            exit(-1)
        f = open('Parameter.dat', 'r', encoding='UTF-8')
        # first line is comment
        f.readline()
        self.para['WeightDistribution'] = int(f.readline())
        self.para['Nelem'] = int(f.readline())
        self.para['NAdd'] = int(f.readline())
        self.para['Pc'] = float(f.readline())
        self.para['Pm'] = float(f.readline())
        self.para['FunctionMode'] = int(f.readline())
        self.para['Cmax'] = int(f.readline())
        self.para['Cmin'] = int(f.readline())
        self.para['PackageSize'] = int(f.readline())
        self.para['MaxGen'] = int(f.readline())
        self.para['PopSize'] = int(f.readline())
        self.para['P4Angle'] = int(f.readline())
        self.para['NAddType'] = int(f.readline())
        self.para['WeightRate'] = float(f.readline())
        self.para['MaxThickLimt'] = int(f.readline())
        self.para['MaxThickValue'] = int(f.readline())
        self.para['OptElemType'] = int(f.readline())
        self.para['Bee'] = float(f.readline())
        f.close()
        if os.path.exists('Outer_Loop_No.txt'):
            f = open('Outer_Loop_No.txt', 'r')
            self.para['Outer_Loop_No'] = int(f.readline()[11:])
            f.close()
        else:
            print("WARNING : Outer_Loop_No.txt not found for parameter configuration. Use default value [=1]")
            self.para['Outer_Loop_No'] = 1


class Node:
    # private vars
    __ss = ['transfer_input_files = ', 'transfer_output_files = ', 'requirements','arguments = ', 'executable = ',
            'should_transfer_files = ', 'universe = ', 'when_to_transfer_output = ', 'log = ',
            'error = ', 'output = ', 'initialdir = ', '']
    # index lists
    __transfer_input_files = 0
    __transfer_output_files = 1
    __requirements = 2
    __arguments = 3
    __executable = 4
    __should_transfer_files = 5
    __universe = 6
    __when_to_transfer_output = 7
    __log = 8
    __error = 9
    __output = 10
    __initialdir = 11
    __a = 12

    def getid(self):
        return self.__id

    def parse_regular(self, child, param):
        param.add(child.tag, parse_MACRO(child.text, param))
        if child.tag == 'input_file':
            self.__contents[self.__transfer_input_files] = parse_MACRO(child.text, param)
        elif child.tag == 'output_file':
            self.__contents[self.__transfer_output_files] = parse_MACRO(child.text, param)
        elif child.tag == 'requirements':
            self.__contents[self.__requirements] = parse_MACRO(child.text, param)
        elif child.tag == 'arguments':
            self.__contents[self.__arguments] = parse_MACRO(child.text, param)
        elif child.tag == 'executable':
            self.__contents[self.__executable] = parse_MACRO(child.text, param)
        elif child.tag == 'jobnum':
            self.__jobnum = int(parse_statement(child, param))
            param.add(child.tag, self.__jobnum)

    def parse_other(self, child, param):
        param.add(child.tag, parse_MACRO(child.text, param))
        if child.tag == 'Universe':
            self.__contents[self.__universe] = parse_MACRO(child.text, param)
        elif child.tag == 'should_transfer_files':
            self.__contents[self.__should_transfer_files] = parse_MACRO(child.text, param)
        elif child.tag == 'when_to_transfer_output':
            self.__contents[self.__when_to_transfer_output] = parse_MACRO(child.text, param)
        elif child.tag == 'Log':
            self.__contents[self.__log] = parse_MACRO(child.text, param)
        elif child.tag == 'error':
            self.__contents[self.__error] = parse_MACRO(child.text, param)
        elif child.tag == 'output':
            self.__contents[self.__output] = parse_MACRO(child.text, param)
        elif child.tag == 'initialdir':
            self.__contents[self.__initialdir] = parse_MACRO(child.text, param)
        elif child.tag == 'a':
            self.__contents[self.__a] = parse_MACRO(child.text, param)

    def parse(self, one, param):
        for child in list(one):
            self.parse_regular(child, param)
        self.__contents[self.__transfer_input_files] += ','+self.__contents[self.__executable]
        two = one.findall('other')
        if len(two) > 1:
            print('WARNING : there are multiple domain "other" in a node declaration. Only take the first one.')
        if len(two) > 0:
            for child in list(two[0]):
                self.parse_other(child, param)

    def __init__(self, node_id, workdir):
        self.__id = node_id
        self.__workdir = workdir
        self.__contents = ['', '', '', '', '', '', '', '', '', '', '', '','']
        self.__jobnum = 1
        self.is_noop = False

    def set_to_noop(self):
        self.__contents = ['', '', '', 'noop', '', '', '', '', '', '', '','', 'Queue']
        self.is_noop = True

    def to_string(self):
        return 'node_' + str(self.__id)

    def to_file_string(self):
        return 'node_' + str(self.__id) + '.sub'

    # generate sub file for this node
    # workdir must be in fold format (end with '/')
    def generate(self):
        f = open(self.__workdir + self.to_file_string(), 'w')
        f.write(self.generate_to_string())
        f.close()

    def generate_to_string(self):
        buff = ''
        for j in range(0, len(self.__ss)):
            if self.__contents[j] != '':
                buff += self.__ss[j] + self.__contents[j] + '\n'
        return buff


class Phase:
    def parse(self, my_phase, param):
        beginning = []
        ending = []
        domain = my_phase.findall('node')
        for one in domain:
            node_id = one.get('id')
            self.__nodes[node_id] = Node(node_id, self.__workdir)
            self.__nodes[node_id].parse(one, param)
            beginning.append(node_id)
            ending.append(node_id)
        domain = my_phase.findall('parent')
        self.__edges = parse_parent(domain, beginning, ending)
        if len(beginning) == 1:
            self.start = beginning[0]
        else:
            print("Error : Phase must have only one entry! " + str(len(beginning)) + ' entries detected!')
            exit(-2)
        if len(ending) == 1:
            self.end = ending[0]
        else:
            print("Error : Phase must have only one ending! " + str(len(ending)) + ' endings detected!')
            exit(-3)
        domain = my_phase.findall('loop')
        if len(domain)>1:
            print('WARNING : there are multiple domain "loop" in a phase declaration. Only take the first one.')
        if len(domain)>0:
            #self.__loop = int(domain[0].text)
            self.__loop = int(parse_statement(domain[0],param))
        domain = my_phase.findall('scr')
        if len(domain) > 1:
            print('WARNING : there are multiple domain "scr" in a phase declaration. Only take the first one.')
        for scr in list(domain[0]):
            if scr.tag == 'pre':
                self.__pre = scr.text
                f = open(scr.text, 'r')
                # now begin to replace the MACROS to the values configured
                scr_contents = f.readlines()
                f.close()
                scr_new_contents = []
                for cont in scr_contents:
                    scr_new_contents.append(parse_MACRO(cont, param))
                f = open(scr.text, 'w', newline='\n')
                f.writelines(scr_new_contents)
                f.close()
            elif scr.tag == 'post':
                self.__post = scr.text
                f = open(scr.text, 'r')
                # now begin to replace the MACROS to the values configured
                scr_contents = f.readlines()
                scr_new_contents = []
                for cont in scr_contents:
                    scr_new_contents.append(parse_MACRO(cont, param))
                f.close()
                f = open(scr.text, 'w', newline='\n')
                f.writelines(scr_new_contents)
                f.close()
            else:
                pass
        if self.__loop > 1:
            self.add_count_loop_to_pre(self.to_string() + '_')

    def __init__(self, id, workdir):
        self.__id = id
        self.__workdir = workdir
        self.__nodes = {}
        self.__edges = {}
        self.__loop = 1
        self.__pre = ''
        self.__post = ''
        self.start = None
        self.end = None
        self.is_noop = False
        self.__final_node = []
        self.__first_node = []

    def set_to_noop(self):
        self.__nodes['.NOOP'] = Node('.NOOP', self.__workdir)
        self.__nodes['.NOOP'].set_to_noop()
        self.is_noop = True

    def add_count_loop_to_pre(self, prefix=''):
        #self.__pre = 'count_loop.bat ' + prefix + 'Outer_Loop_No.txt ' + self.__pre
        return

    def generate_nodes(self):
        # generate sub file
        for n in self.__nodes:
            self.__nodes[n].generate()

    def generate(self):
        self.generate_nodes()
        # generate sub dag file
        f = open(self.__workdir + 'sub_Phase' + str(self.__id) + '.dag', 'w')
        # generate node info
        for n in self.__nodes:
            f.write('job ' + self.__nodes[n].to_string() + ' ' + self.__nodes[n].to_file_string() + '\n')
        # ADD PRE/POST SCRIPT
        if self.__pre != '':
            f.write('script pre ' + self.__nodes[self.start].to_string() + ' ' + self.__pre + '\n')
        if self.__post != '':
            f.write('script post ' + self.__nodes[self.end].to_string() + ' ' + self.__post + '\n')
        # generate edge info
        for parent in self.__edges:
            f.write('parent ' + self.__nodes[parent].to_string() + ' child')
            for child in self.__edges[parent]:
                f.write(' ' + self.__nodes[child].to_string())
            f.write('\n')
        f.close()
        f = open(self.__workdir + 'Phase' + str(self.__id) + '.dag', 'w')
        for k in range(0, self.__loop):
            f.write('subdag external sub_Phase' + str(self.__id) + '_' + str(k) +
                    ' sub_Phase' + str(self.__id) + '.dag' + '\n')
        for k in range(0, self.__loop-1):
            f.write('parent sub_Phase' + str(self.__id) + '_' + str(k) +
                    ' child sub_Phase' + str(self.__id) + '_' + str(k+1) + '\n')
        f.close()

    # generate dag description
    def generate_to_string(self, loopnum):
        buff = ''
        for k in range(0, self.__loop):
            for n in self.__nodes:
                if self.__nodes[n].is_noop:
                    buff += 'job ' + self.__nodes[n].to_string() + '_' + str(k) + '_' + str(loopnum) + ' ' + \
                            self.__nodes[n].to_file_string() + ' NOOP\n'
                else:
                    buff += 'job ' + self.__nodes[n].to_string() + '_' + str(k) + '_' + str(loopnum) + ' ' + \
                            self.__nodes[n].to_file_string() + '\n'
            # ADD PRE/POST SCRIPT
            if self.__pre != '':
                buff += 'script pre ' + self.__nodes[self.start].to_string() + '_' + str(k) + '_' + str(loopnum) + \
                        ' ' + self.__pre + '\n'
            if self.__post != '':
                buff += 'script post ' + self.__nodes[self.end].to_string() + '_' + str(k) + '_' + str(loopnum) + \
                        ' ' + self.__post + '\n'
            # generate edge info
            for parent in self.__edges:
                buff += 'parent ' + self.__nodes[parent].to_string() + '_' + str(k) + '_' + str(loopnum) + ' child'
                for child in self.__edges[parent]:
                    buff += ' ' + self.__nodes[child].to_string() + '_' + str(k) + '_' + str(loopnum)
                buff += '\n'
        for k in range(0, self.__loop - 1):
            buff += 'parent ' + self.__nodes[self.end].to_string() + '_' + str(k) + '_' + str(loopnum) + \
                    ' child ' + self.__nodes[self.start].to_string() + '_' + str(k + 1) + '_' + str(loopnum) + '\n'
        self.__final_node.append(self.__nodes[self.end].to_string() + '_' + str(self.__loop-1) + '_' + str(loopnum))
        self.__first_node.append(self.__nodes[self.start].to_string() + '_0_' + str(loopnum))
        return buff

    def to_string(self):
        return 'Phase' + str(self.__id)

    def to_file_string(self):
        return self.to_string() + '.dag'

    def final_node(self, loopnum):
        return self.__final_node[loopnum]

    def first_node(self, loopnum):
        return self.__first_node[loopnum]


class DAG:
    def parse(self, xml, param):
        work = ET.parse(xml)
        phases = work.findall('phase')
        for p in phases:
            pid = p.get('id')
            self.__phases[pid] = Phase(pid, self.__workdir)
            self.__phases[pid].parse(p, param)
            self.start.append(pid)
            self.end.append(pid)
        domain = work.findall('parent')
        self.__edges = parse_parent(domain, self.start, self.end)
        if len(self.start) > 1:
            self.__edges['.NOOP'] = self.start
            self.start = ['.NOOP']
            self.__phases['.NOOP'] = Phase('.NOOP', self.__workdir)
            self.__phases['.NOOP'].set_to_noop()
        if len(self.start) <= 0:
            print("Error : workflow must have at least one entry! " + str(len(self.start)) + ' entries detected!')
            exit(-2)
        if len(self.end) <= 0:
            print("Error : workflow must have at least one ending! " + str(len(self.end)) + ' endings detected!')
            exit(-3)
        domain = work.findall('loop')
        if len(domain) > 0:
            if len(domain) > 1:
                print('WARNING : there are multiple domain "loop" in a workflow declaration. Only take the first one.')
            self.__loop = int(parse_statement(domain[0], param))

    def __init__(self, workdir, xml, param):
        self.__workdir = workdir
        self.__phases = {}
        self.__edges = {}
        self.__loop = 1
        self.start = []
        self.end = []
        self.parse(xml, param)

    def generate(self, mode):
        if mode == 'foo':
            self.generate_foo()
        elif mode == 'sub':
            self.generate_sub()
        elif mode == 'mix':
            raise NotImplementedError('MIX MODE NOT IMPLEMENTED')

    def generate_sub(self):
        for key in self.__phases:
            self.__phases[key].generate()
        f = open(self.__workdir + 'submit.dag', 'w')
        for k in range(0, self.__loop):
            for key in self.__phases:
                f.write('subdag external ' + self.__phases[key].to_string() + '_' + str(k) + ' ' +
                        self.__phases[key].to_file_string() + '\n')
            for key in self.__edges:
                f.write('parent ' + self.__phases[key].to_string() + '_' + str(k) + ' child')
                for child in self.__edges[key]:
                    f.write(' ' + self.__phases[child].to_string() + '_' + str(k))
                f.write('\n')
        buff = ''
        for k in range(0, self.__loop-1):
            buff += 'parent '
            for p in self.end:
                buff += self.__phases[p].to_string() + '_' + str(k) + ' '
            buff += 'child'
            for c in self.start:
                buff += ' ' + self.__phases[c].to_string() + '_' + str(k+1)
            buff += '\n'
        f.write(buff)
        f.close()

    def generate_foo(self):
        for key in self.__phases:
            self.__phases[key].generate_nodes()
        if self.__loop > 1:
            self.__phases[self.start[0]].add_count_loop_to_pre()
        buff = ''
        for k in range(0, self.__loop):
            for key in self.__phases:
                buff += self.__phases[key].generate_to_string(k) + '\n'
            for key in self.__edges:
                buff += 'parent ' + self.__phases[key].final_node(k) + ' child'
                for child in self.__edges[key]:
                    buff += ' ' + self.__phases[child].first_node(k)
                buff += '\n'
            buff += '\n'
        for k in range(0, self.__loop-1):
            buff += 'parent '
            for p in self.end:
                buff += self.__phases[p].final_node(k) + ' '
            buff += 'child'
            for c in self.start:
                buff += ' ' + self.__phases[c].first_node(k+1)
            buff += '\n'
        f = open(self.__workdir + 'submit.dag', 'w')
        f.write(buff)
        f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--xml', help='Input XML file', default='in.xml')
    parser.add_argument('--out', help='Output folder', default='./submit/')
    parser.add_argument('--mode', help='Generation Mode: foo / mix / sub', default='foo')
    parser.add_argument('--parameter', help='parameter files for dag generation',default='')
    args = parser.parse_args()
    XML = args.xml
    out = args.out
    if not os.path.exists(XML):
        print("Error : Input file not exists!")
        exit(-1)
    if out == './':
        if os.path.exists('./log'):
            shutil.rmtree('./log')
        os.mkdir('./log')
        out = './'
    elif os.path.exists(out):
        shutil.rmtree(out)
        os.mkdir(out)
        os.mkdir(out + 'log')
    else:
        os.mkdir(out)
        os.mkdir(out + 'log')
    parameter = Parameter()
    if args.parameter == 'Parameter.dat':
        parameter.read()
    else:
        parameter.general_read(args.parameter)
    dag = DAG(out, XML, parameter)
    dag.generate(args.mode)
