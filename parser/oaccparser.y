/* OpenACC Parser */

%{
#define YYSTYPE char
#include <stdio.h>
#define DEBUGMODE 0
yyerror (s)  /* Called by yyparse on error */
     char *s;
{
  printf ("%s\n", s);
}

%}

%token CH

%% /* Grammar rules and actions follow */

input:   'S' S      { if(DEBUGMODE) printf(">0\n"); }
//       | 'C'        { if(DEBUGMODE) printf(">1\n"); }    
       | error '\n'     { printf("malform parser input\n"); return -1; }
;

S:       'C'        { if(DEBUGMODE) printf(">2\n"); }
       | 'C' P S    { if(DEBUGMODE) printf(">3\n"); }
       | error      { printf("The code should always begin with the C\n"); return -1; }
;

P:       'K' K 'k'  { if(DEBUGMODE) printf(">4\n"); }
       | 'D' S 'd'  { if(DEBUGMODE) printf(">5\n"); }
       | 'D' F 'd'  { if(DEBUGMODE) printf(">5A\n"); }
       | error      { printf("unsupported directive\n"); return -1; }
/*       | 'A'        { printf(">6\n"); }*/
;

K:       'C'                { if(DEBUGMODE) printf(">7\n"); }
/*       | 'C' L 'C'          { if(DEBUGMODE) printf(">8\n"); }*/
       | 'C' L  K           { if(DEBUGMODE) printf(">8\n"); }
       | L                  { if(DEBUGMODE) printf(">9\n"); }
       | error              { printf("Error in the kernel region\n"); return -1; }
;

L:       'L' F  'l'         { if(DEBUGMODE) printf(">10\n"); }
       | 'L' 'C' F  'C' 'l' { if(DEBUGMODE) printf(">11\n"); }
       | error              { printf("expecting a `for` construct after the acc loop\n"); return -1; }
;

F:       'F' 'C' 'f'        { if(DEBUGMODE) printf(">12\n"); }
       | 'F' 'C' F  'C' 'f' { if(DEBUGMODE) printf(">13\n"); }
       | 'F' 'C' L  'C' 'f' { if(DEBUGMODE) printf(">14\n"); }
       | 'F' F 'f'          { if(DEBUGMODE) printf(">15\n"); }
       | 'F' L 'f'          { if(DEBUGMODE) printf(">16\n"); }
       | 'F' 'f'            { if(DEBUGMODE) printf(">17\n"); }
       | 'C' H              { if(DEBUGMODE) printf(">18\n"); }
       | 'F' S 'f'          { if(DEBUGMODE) printf(">19\n"); }
       | error              { printf("unexpected pragma in the for loop\n"); return -1; }

H:       H H                { if(DEBUGMODE) printf(">20\n"); }
       | F 'C'
       | error              { printf("unexpected content in for loop\n"); return -1; }
;

/*
*/

%%

/* Lexical analyzer returns a character.
   Skips all blanks  and tabs, returns 0 for EOF. */

#include <ctype.h>

yylex ()
{
  int c;

  /* skip white space  */
  while ((c = getchar ()) == ' ' || c == '\t' || c=='\n')  
    ;

  /* return end-of-file  */
  if (c == EOF)                            
    return 0;
  /* return single chars */
//  printf("read character-> %c\n",c);
  //printf("%d\n",c);
  return c;                                
}

main ()
{
  int c=yyparse ();
  return c;
}
