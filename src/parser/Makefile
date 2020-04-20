CC=gcc
all:
	bison oaccparser.y 
	$(CC) oaccparser.tab.c -o oaccparser 
clean:
	rm oaccparser.tab.c oaccparser -f
