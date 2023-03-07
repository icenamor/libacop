#include <iostream>
#include <fstream>
#include <string>

#include <string.h>

#include <stdlib.h>
#include <sys/times.h>

using namespace std;

int main(int nargs, char *args[]) 
{
  int i;
  string file_name;
  string domain_name;
  string output;
  string file_configurazione;
  string configurazione;
  string temp;
  string dwdir(args[0]);
  size_t found;
  found=dwdir.find_last_of('/');
  dwdir=dwdir.substr(0,found);
  dwdir.append("/");
  //cout << dwdir;
  //sprintf(dwdir, "%s", args[0]);
  //while (dwdir[strlen(dwdir)-1] != '/')
  //   dwdir[strlen(dwdir)-1] = '\0'; 

  

  cout << "DIR = " << dwdir;

  for (i = 0; i < nargs; i++) 
    {
      if (strcmp(args[i], "-o") == 0)
	domain_name.assign(args[++i]);
	//strcpy(domain_name, args[++i]);
      else if (strcmp(args[i], "-f") == 0)
	file_name.assign(args[++i]);
      else if (strcmp(args[i], "-out") == 0)
	output.assign(args[++i]);
      else if (strcmp(args[i], "-conf") == 0)
	file_configurazione.assign(args[++i]);
    }
 
  
  ifstream myfile (file_configurazione.c_str());
  if (myfile.is_open()) //if the file is open
  {
  	getline(myfile,configurazione);
  }else{
	cout << "\n\nERROR: unable to open configuration file " << file_configurazione << "\n\n";
	return 1;
  }
  myfile.close();

  cout << "\nDomain: " << domain_name <<" \nProblem: " << file_name << "\n\nLPG configured... with: " << file_configurazione <<"\n";
  //fflush(stdout);
  temp.append(dwdir);
  temp.append("lpg_par_test -o ");
  temp.append(domain_name);
  temp.append(" -f ");
  temp.append(file_name);
  temp.append(" -n 100 -out ");
  temp.append(output);
  temp.append(" ");
  temp.append(configurazione);
  //cout << temp;
  //sprintf(temp, "%slpg_pbp ", dwdir,output);
  system(temp.c_str());

  return 0;

}
