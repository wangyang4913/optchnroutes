import urllib.request
import re 
import math
import ipaddress
from enum import Enum

class NODE_TYPE(Enum):
    RED=0,
    BLUE=1,
    NODE=2,
    
class BTreeNode:
    node_type = NODE_TYPE.NODE
    deep = 0;
    parent = None;
    left = None;
    right = None;
        
    def delete(self):
        if (self.parent.left == self):
            self.parent.left = None;
        else :
            self.parent.right = None;
            
    def getBrother(self):
        if self.parent == None:
            return None
        if self.parent.left == self:
            return self.parent.right
        else:
            self.parent.left
            
class OutputHandler:
    upBuf = '@echo off\nfor /F "tokens=3" %%* in (\'route print ^| findstr "\<0.0.0.0\>"\') do set "local=%%*"\n\nipconfig /flushdns\n'
    downBuf = '@echo off\n'
    
    def execute(self ,node ,prefix):
        if node.node_type != NODE_TYPE.RED:
            return
        antiMask = 32-node.deep
        ip = str(ipaddress.IPv4Address(int(prefix + ('0'*antiMask), 2)))
        self.upBuf += 'route add {0}/{1} %local% metric 25\n'.format(ip,node.deep)
        self.downBuf += 'route delete {0}\n'.format(ip)
        
    def flush(self):
        file = open('upRoute.bat' ,'w')
        file.write(self.upBuf)
        file.close()
        file = open('downRoute.bat' ,'w')
        file.write(self.downBuf)
        file.close()
            
class BTree:      
    root = BTreeNode()
    handler = OutputHandler()
    
    #(NODE_TYPE ,str:1.0.0.0 ,int:8 ,str:01010101001)
    def insert(self ,node_info):
        nodeTar = self.root;
        for i in node_info[3]:
            if i == '0':
                if nodeTar.left == None:
                    nodeTar.left = self.createnode(nodeTar)
                nodeTar = nodeTar.left
            else:
                if nodeTar.right == None:
                    nodeTar.right = self.createnode(nodeTar)
                nodeTar = nodeTar.right
        nodeTar.node_type = node_info[0]
            
    def createnode(self ,parent):
        node = BTreeNode()
        node.node_type = NODE_TYPE.NODE
        node.deep = parent.deep + 1
        node.parent = parent;
        return node
    
    def shrink(self ,node ,isLeft):
        if node == None:
            return
        self.shrink(node.left,True)
        self.shrink(node.right,False)
        if node.parent == None or node.node_type == NODE_TYPE.NODE:
            return;
        brother = None
        if isLeft:
            brother = node.parent.right
        else:
            brother = node.parent.left
        if brother == None:
            node.parent.node_type = node.node_type;
            node.parent.left = None;
            node.parent.right = None;
            return;
        if brother.node_type == NODE_TYPE.NODE:
            return;
        if node.node_type != brother.node_type:
            return;
        node.parent.node_type = node.node_type;
        node.parent.left = None;
        node.parent.right = None;
        
    def traverse(self):
        self.DepthFirstSearch(self.root,'')
        self.handler.flush()
    
    def DepthFirstSearch(self ,node ,prefix):
        if node == None:
            return
        self.DepthFirstSearch(node.left, prefix + '0')
        self.DepthFirstSearch(node.right, prefix + '1')
        self.handler.execute(node, prefix)

def fetch_ip_data():
    data = urllib.request.urlopen('http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest')
    result = []
    pattern = re.compile(r'^apnic\|(\w*)\|ipv4\|([\d\.]+)\|(\d+)\|\d+\|a\w*$',re.I | re.M)
    while 1:
        line = data.readline().decode()
        if not line:
            break
        reMatch = re.match(pattern, line)
        if not reMatch:
            continue
        node_type = NODE_TYPE.RED
        if reMatch.group(1) == 'CN' :
            node_type = NODE_TYPE.RED
        else:
            if reMatch.group(1) == 'US' or reMatch.group(1) == 'JP' or reMatch.group(1) == 'HK':
                node_type = NODE_TYPE.BLUE
            else :
                continue
        ip = reMatch.group(2)
        anti_mask = int(math.log(int(reMatch.group(3)),2))
        bin_str_ip = bin(int(ipaddress.IPv4Address(ip)))[2:]
        bin_str_ip = ('0'*(32-len(bin_str_ip)) + bin_str_ip)[:32-anti_mask]
        #(NODE_TYPE ,str:1.0.0.0 ,int:8 ,str:01010101001)
        result.append((node_type, ip, anti_mask, bin_str_ip)) 
    return result

def main():
    tree = BTree()
    results = fetch_ip_data()
    for result in results:
        tree.insert(result)
    tree.shrink(tree.root ,True)
    tree.traverse()

if __name__ == '__main__':
    main()
    
