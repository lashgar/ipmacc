

int
main ()
{
  int i, j;
  for (i = 0; i < 10; i++)
    for (j = 0; j < 10; i++)
      if (i % 2)
	j++;
      else if (i > 1)
	j--;
      else
	i = 0;


  return 0;
}
