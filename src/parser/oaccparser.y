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
//       | CODE        { if(DEBUGMODE) printf(">1\n"); }    
       | error '\n'     { printf("malform parser input\n"); return -1; }
;

S:       CODE        { if(DEBUGMODE) printf(">2\n"); }
       //| CODE S      { if(DEBUGMODE) printf(">3\n"); }
       | CODE P S    { if(DEBUGMODE) printf(">3\n"); }
       | error      { printf("The code should always begin with the C\n"); return -1; }
;

P:       'K' K 'k'  { if(DEBUGMODE) printf(">4\n"); }
       | 'D' S 'd'  { if(DEBUGMODE) printf(">5\n"); }
       | 'D' F 'd'  { if(DEBUGMODE) printf(">5A\n"); }
       | 'F' S 'f'  { if(DEBUGMODE) printf(">5B\n"); }
       | error      { printf("unsupported directive\n"); return -1; }
/*       | 'A'        { printf(">6\n"); }*/
;

K:       CODE                { if(DEBUGMODE) printf(">7\n"); }
/*       | CODE L CODE          { if(DEBUGMODE) printf(">8\n"); }*/
       | CODE L  K           { if(DEBUGMODE) printf(">8\n"); }
       | L                  { if(DEBUGMODE) printf(">9\n"); }
       | error              { printf("Error in the kernel region\n"); return -1; }
;

L:       'L' F  'l'         { if(DEBUGMODE) printf(">10\n"); }
       | 'L' CODE F  CODE 'l' { if(DEBUGMODE) printf(">11\n"); }
       | error              { printf("expecting a `for` construct after the acc loop\n"); return -1; }
;

F:       'F' CODE 'f'        { if(DEBUGMODE) printf(">12\n"); }
       | 'F' CODE F  CODE 'f' { if(DEBUGMODE) printf(">13\n"); }
       | 'F' CODE M  CODE 'f' { if(DEBUGMODE) printf(">13A\n"); }
       | 'F' CODE L  CODE 'f' { if(DEBUGMODE) printf(">14\n"); }
       | 'F' F 'f'          { if(DEBUGMODE) printf(">15\n"); }
       | 'F' L 'f'          { if(DEBUGMODE) printf(">16\n"); }
       | 'F' 'f'            { if(DEBUGMODE) printf(">17\n"); }
       | CODE H              { if(DEBUGMODE) printf(">18\n"); }
       | 'F' S 'f'          { if(DEBUGMODE) printf(">19\n"); }
       | error              { printf("unexpected pragma in the for loop\n"); return -1; }

H:       H H                { if(DEBUGMODE) printf(">20\n"); }
       | F CODE              { if(DEBUGMODE) printf(">21\n"); }
       | CODE F              { if(DEBUGMODE) printf(">22\n"); }
       | F                  { if(DEBUGMODE) printf(">23\n"); }
       | CODE M CODE          { if(DEBUGMODE) printf(">24\n"); }
       | CODE M H            { if(DEBUGMODE) printf(">25\n"); }
       | M H                { if(DEBUGMODE) printf(">26\n"); }
       | M H CODE            { if(DEBUGMODE) printf(">27\n"); }
       | M                  { if(DEBUGMODE) printf(">28\n"); }
       //| error              { printf("unexpected content in for loop\n"); return -1; }
;

M:       'M' 'm'                  { if(DEBUGMODE) printf(">29\n"); }
       | 'M' F 'm'                  { if(DEBUGMODE) printf(">30\n"); }
       | 'M' CODE 'm'                  { if(DEBUGMODE) printf(">31\n"); }
       | error              { printf("unexpected content within cache region\n"); return -1; }
;


CODE:
         'C'                {if(DEBUGMODE) printf(">32\n"); }
       | 'A' 'a'            {if(DEBUGMODE) printf(">33\n"); }
       | 'C' CODE 'C'       {if(DEBUGMODE) printf(">34\n"); }
       | 'C' 'E' CODE       {if(DEBUGMODE) printf(">34\n"); }
       //| 'C' F 'C'       {if(DEBUGMODE) printf(">34\n"); }
       | error              { printf("unexpected content within C/C++ code region\n"); return -1; }

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
