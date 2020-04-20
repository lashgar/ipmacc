import sys
sys.path.append('/share/users/alashgar/scanner/pycparser')
from pycparser import c_parser

parser = c_parser.CParser()
#text = 'int x; int y; float z;'
text="""
    float **a=NULL;
    float **b, *j;
    float **c;
    float **seq;
    int K;
    K=a+1;
    """
k="""
    a=(float**)malloc(SIZE*sizeof(float*));
    b=(float**)malloc(SIZE*sizeof(float*));
    c=(float**)malloc(SIZE*sizeof(float*));
    seq=(float**)malloc(SIZE*sizeof(float*));
    """

ast = parser.parse(text, filename='<none>')
ast.show()

