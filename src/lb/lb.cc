#include <Lightboard_i.hh>
#include <Dimmer_i.hh>
#include <Instrument_i.hh>
#include <Fader_i.hh>
#include <CueFader_i.hh>
#include <CrossFader_i.hh>
#include <LevelFader_i.hh>

#include <stdio.h>
#include <dlfcn.h>
#include <expat.h>

/**** Globals... ****/
LB::Lightboard_ptr lb;
CORBA::ORB_ptr orb;
CosNaming::NamingContext_ptr rootNaming;
CosNaming::NamingContext_ptr dimmerContext;
/**** ...Globals ****/

static GSList *modules;
static char *lb_name;

static void start(void *data, const char *el, const char **attr) 
{
  int i;
  const char *name;

  if (strcmp(el, "lb")==0)
    {
      for (i = 0; attr[i]; i += 2) 
        {
	  if (strcmp(attr[i],"name")==0)
            lb_name=strdup(attr[i+1]);
        }
    }
  if (strcmp(el, "module")==0)
    {
      name=NULL;
      for (i = 0; attr[i]; i += 2) 
        {
	  if (strcmp(attr[i],"name")==0)
            name=attr[i+1];
        }
      if (name)
	modules = g_slist_append(modules, strdup(name));
    }
}

static void end(void *data, const char *el) 
{
}

static void parse (const char *fn, void *userdata)
{
  char buf[8096];

  XML_Parser p = XML_ParserCreate(NULL);
  if (!p) 
    {
      fprintf(stderr, "Couldn't allocate memory for parser\n");
      exit(-1);
    }

  XML_SetUserData(p, userdata);

  XML_SetElementHandler(p, start, end);
  FILE *f = fopen(fn, "r");
  if (!f)
    {
      perror("Config");
      exit(-1);
    }

  for (;;) {
    int done;
    int len;

    len = fread(buf, 1, 8096, f);
    if (ferror(f)) {
      fprintf(stderr, "Read error\n");
      exit(-1);
    }
    done = feof(f);

    if (! XML_Parse(p, buf, len, done)) {
      fprintf(stderr, "Parse error at line %d:\n%s\n",
              XML_GetCurrentLineNumber(p),
              XML_ErrorString(XML_GetErrorCode(p)));
      exit(-1);
    }

    if (done)
      break;
  }
  fclose(f);
}


int make_level(long int level)
{
  /* takes a percentage in .01 percent and returns 0-dimmerrange */
  return 0;
}

double make_time(const char *t)
{
  int len=strlen(t);
  char *tim=strdup(t);
  double  ftime=0.0;

  if(t[len-1]=='s')
    return atof(t);
  if(t[len-1]=='m')
    return atof(t)*60;
  if(t[len-1]=='h')
    return atof(t)*60*60;
  
  double  multiple=1.0;
  char *p=strrchr(tim, ':');

  while (p!=NULL)
    {
      double n=atof(p+1);
      ftime=ftime+(n*multiple);
      *p=0;
      multiple=multiple*60.0;
      if (multiple>3600)
	{
	  free(tim);
	  return 0;
	}
      p=strrchr(tim, ':');
    }
  if (strlen(tim))
    ftime=ftime+(atof(tim)*multiple);
  free(tim);
  return ftime;
}


LB::Cue *duplicate_cue (const LB::Cue& incue, int zero)
{
  /* Deprecated */
  LB::Cue *cue = new LB::Cue;

  cue->name = incue.name;
  int numins=incue.ins.length();
  cue->ins.length(numins);
  for (int i=0; i<numins; i++)
    {
      cue->ins[i].name = incue.ins[i].name;
      int numattr=incue.ins[i].attrs.length();
      cue->ins[i].attrs.length(numattr);
      for (int a=0; a<numattr; a++)
	{
	  cue->ins[i].attrs[a].attr=incue.ins[i].attrs[a].attr;
	  int numval=incue.ins[i].attrs[a].value.length();
	  cue->ins[i].attrs[a].value.length(numval);
	  for (int v=0; v<numval; v++)
	    {
	      if (zero)
		cue->ins[i].attrs[a].value[v]=0.0;

	      else
		cue->ins[i].attrs[a].value[v]=incue.ins[i].attrs[a].value[v];
	    }
	}
    }
  
  return cue;
}

static double my_time(void)
{
  struct timeval tv;
  gettimeofday(&tv, NULL);
  
  double r = tv.tv_sec + tv.tv_usec/1000000.0;
  return r;
}

void normalize_cues (const LB::Cue& incue1, const LB::Cue& incue2,
		     LB::Cue &outcue1, LB::Cue &outcue2)
{
  GHashTable *hash1, *hash2;
  int outcue_len=0;

  hash1=g_hash_table_new (g_str_hash, g_str_equal);
  hash2=g_hash_table_new (g_str_hash, g_str_equal);

  outcue1.name = incue1.name;
  outcue2.name = incue2.name;
  
  int numins; 
  int numattr2, numattr1;
  gpointer loc;
  int pos, pos1, pos2;

  double time1, time2, time3, time4;

  time1=my_time();

  numins = incue2.ins.length();
  pos=0;
  outcue_len=numins;
  outcue1.ins.length(outcue_len);
  outcue2.ins.length(outcue_len);
  for (int i=0; i<numins; i++)
    {
      outcue1.ins[pos].name = incue2.ins[i].name;
      outcue2.ins[pos].name = incue2.ins[i].name;
      outcue1.ins[pos].inst = incue2.ins[i].inst;
      outcue2.ins[pos].inst = incue2.ins[i].inst;
      g_hash_table_insert (hash2, incue2.ins[i].name, (gpointer)(i+1));
      pos++;
    }

  time2=my_time();

  numins = incue1.ins.length();
  for (int i=0; i<numins; i++)
    {
      if (g_hash_table_lookup(hash2, incue1.ins[i].name)==NULL)
	++outcue_len;
    }

  outcue1.ins.length(outcue_len);
  outcue2.ins.length(outcue_len);

  numins = incue1.ins.length();
  for (int i=0; i<numins; i++)
    {
      if (g_hash_table_lookup(hash2, incue1.ins[i].name)==NULL)
	{
	  outcue1.ins[pos].name = incue1.ins[i].name;
	  outcue2.ins[pos].name = incue1.ins[i].name;
	  outcue1.ins[pos].inst = incue1.ins[i].inst;
	  outcue2.ins[pos].inst = incue1.ins[i].inst;
	  pos++;
	}
      g_hash_table_insert (hash1, incue1.ins[i].name, (gpointer)(i+1));
    }

  time3=my_time();

  numins = outcue2.ins.length();
  for (int i=0; i<numins; i++)
    {
      loc=g_hash_table_lookup(hash2, outcue2.ins[i].name);
      pos2=((int)loc)-1;
      loc=g_hash_table_lookup(hash1, outcue2.ins[i].name);
      pos1=((int)loc)-1;
      /*
	foreach attr in second cue
	  put it in second cue
	  if the first cue has it
  	    put same attr in first cue
          else
            put current state in first cue
      */
      
      if (pos2>-1)
	numattr2 = incue2.ins[pos2].attrs.length();
      else
	numattr2 = 0;
      if (pos1>-1)
	numattr1 = incue1.ins[pos1].attrs.length();
      else
	numattr1 = 0;

      outcue1.ins[i].attrs.length(numattr2);
      outcue2.ins[i].attrs.length(numattr2);

      for (int a2=0; a2<numattr2; a2++)
	{
	  outcue2.ins[i].attrs[a2].attr = incue2.ins[pos2].attrs[a2].attr;
	  outcue2.ins[i].attrs[a2].value = incue2.ins[pos2].attrs[a2].value;
	  int placed=0;
	  for (int a1=0; a1<numattr1; a1++)
	    {
	      if (incue1.ins[pos1].attrs[a1].attr == 
		  incue2.ins[pos2].attrs[a2].attr)
		{
		  placed=1;

		  outcue1.ins[i].attrs[a2].attr = 
		    incue1.ins[pos1].attrs[a1].attr;

		  outcue1.ins[i].attrs[a2].value =        // deep copy
		    incue1.ins[pos1].attrs[a1].value;     // or so i'm told

		  break;
		}
	    }
	  if (!placed)
	    {
	      outcue1.ins[i].attrs[a2].attr = incue2.ins[pos2].attrs[a2].attr;
	      get_attribute_value(outcue1.ins[i].attrs[a2], outcue2.ins[i].inst);
	    }
	}   // loop over attributes in cue2

      /* 
	 But, if there are no attrs in the second cue, add level = 0
	 to second cue, and current level from the first cue in it. 
      */
      if (numattr2 == 0)
	{
	  numattr2=1;

	  outcue1.ins[i].attrs.length(numattr2);
	  outcue2.ins[i].attrs.length(numattr2);

	  for (int a2=0; a2<numattr2; a2++)
	    {
	      outcue2.ins[i].attrs[a2].attr = LB::attr_level;
	      outcue2.ins[i].attrs[a2].value.length(1);
	      outcue2.ins[i].attrs[a2].value[0]=0.0;

	      for (int a1=0; a1<numattr1; a1++)
		{
		  if (incue1.ins[pos1].attrs[a1].attr == LB::attr_level)
		    {
		      outcue1.ins[i].attrs[a2].attr = LB::attr_level;
		      outcue1.ins[i].attrs[a2].value =        // deep copy
			incue1.ins[pos1].attrs[a1].value;     // or so i'm told

		      break;
		    }
		}
	    }  //loop over attributes, for insts going to 0
	} // If inst not in second cue, going to 0
    }  // loop over all instruments

  time4=my_time();

  printf ("norm: %f %f %f\n", time2-time1, time3-time2, time4-time3);

  g_hash_table_destroy (hash1);
  g_hash_table_destroy (hash2);
}

CosNaming::NamingContext_ptr
getRootNamingContext(CORBA::ORB_ptr orb)
{
  CosNaming::NamingContext_ptr rootContext;
  try {

     // Get initial reference.
     CORBA::Object_var initServ;
     initServ = orb->resolve_initial_references("NameService");

     // Narrow the object returned by resolve_initial_references()
     // to a CosNaming::NamingContext object:
     rootContext = CosNaming::NamingContext::_narrow(initServ);
     if (CORBA::is_nil(rootContext))
     {
       fprintf (stderr, "Failed to narrow naming context.\n");
       exit(1);
     }
  }
  catch(CORBA::ORB::InvalidName& ex) {
    fprintf (stderr, "Service required is invalid [does not exist].\n");
    exit(1);
  }
  catch (CORBA::COMM_FAILURE& ex) {
    fprintf (stderr, "Caught system exception COMM_FAILURE.\n");
    exit(1);
  }
  catch (omniORB::fatalException& ex) {
    fprintf (stderr, "Caught Fatal Exception\n");
    throw;
  }
  catch (...) {
    fprintf (stderr, "Caught a system exception while resolving the naming service.\n");
    exit(1);
  }
  return rootContext;
}

CORBA::Boolean
bindObjectToName(CORBA::ORB_ptr orb, CORBA::Object_ptr objref, 
                 const char* id, const char* kind)
{
  
  try { 
    CosNaming::NamingContext_var rootContext = getRootNamingContext(orb);

    CosNaming::Name objectName;
    objectName.length(1);
    objectName[0].id   = id;   // string copied
    objectName[0].kind = kind; // string copied
    
    try {
      rootContext->bind(objectName, objref);
    }
    catch(CosNaming::NamingContext::AlreadyBound& ex) {
      rootContext->rebind(objectName, objref);
    }
  }
  catch(CORBA::COMM_FAILURE& ex) {
    fprintf (stderr, "Caught system exception COMM_FAILURE -- unable to contact the naming service.\n");
    return 0;
  }
  catch(CORBA::SystemException&) {
    fprintf (stderr, "Caught a CORBA::SystemException while using the naming service.\n");
    return 0;
  }
  return 1;
}

static void load_modules(void)
{
  void (*func)(void);
  char *error, *name;
  GSList *l=modules;

  while (l)
    {
      int len;
      void *handle;

      len = strlen((char *)l->data) + 4;
      name = (char *)malloc (len);
      snprintf(name, len, "%s.so", (char *)l->data);

      handle = dlopen(name, RTLD_NOW | RTLD_GLOBAL);

      if (handle == NULL)
	{
	  fprintf (stderr, "Module error: %s: %s\n", name, dlerror());
	}
      else
	{
	  func = (void (*)(void)) dlsym(handle, "lb_module_init");
	  if ((error = dlerror()) != NULL)  
	    fprintf (stderr, "Module error: %s: %s\n", name, error);
	  else
	    func();
	}
      l = g_slist_next(l);
      free(name);
    }
}

int main(int argc, char** argv)
{
  modules = NULL;
  parse("/etc/lb/config.xml", NULL);

  try {
    // Initialise the ORB.
    orb = CORBA::ORB_init(argc, argv, "omniORB3");

    // Obtain a reference to the root POA.
    CORBA::Object_var obj = orb->resolve_initial_references("RootPOA");
    PortableServer::POA_var poa = PortableServer::POA::_narrow(obj);

    // Obtain the Naming Service
    CosNaming::NamingContext_ptr namectx = getRootNamingContext(orb);


    // We allocate the objects on the heap.  Since these are reference
    // counted objects, they will be deleted by the POA when they are no
    // longer needed.
    LB_Lightboard_i* myLB_Lightboard_i = new LB_Lightboard_i(lb_name);

    // Activate the objects.  This tells the POA that the objects are
    // ready to accept requests.
    PortableServer::ObjectId_var myLB_Lightboard_iid = poa->activate_object(myLB_Lightboard_i);
    

    // Obtain a reference to each object and output the stringified
    // IOR to stdout

    // IDL interface: LB::Lightboard
    lb = myLB_Lightboard_i->_this();
    

    /* create name graph:
       /shows
         /showname
	   /instruments
	     instrumentname
	   /faders
             fadername
       /lightboards
         /lbname
	   lb
	   /dimmers
	     dimmername

      or at least the bottom part.
    */

    {
      CosNaming::Name name;
      name.length(1);
      name[0].id   = (const char *)"lightboards";

      rootNaming = getRootNamingContext(orb);
      CosNaming::NamingContext_var lbcontext, mylbcontext;

      try
	{
	  lbcontext=rootNaming->bind_new_context(name);
	}
      catch(CosNaming::NamingContext::AlreadyBound& ex) 
	{
	  CORBA::Object_var obj;
	  obj=rootNaming->resolve(name);
	  lbcontext = CosNaming::NamingContext::_narrow(obj);
	}
      
      name[0].id   = (const char *)lb_name;
      try
	{
	  mylbcontext=lbcontext->bind_new_context(name);
	}
      catch(CosNaming::NamingContext::AlreadyBound& ex) 
	{
	  lbcontext->unbind(name);
	  // FIXME: do we need to destroy?
	  mylbcontext=lbcontext->bind_new_context(name);
	}

      /* the rest should be empty */

      name[0].id   = (const char *)"lb";
      name[0].kind   = (const char *)"Lightboard";
      mylbcontext->rebind(name, lb);

      name[0].id   = (const char *)"dimmers";
      name[0].kind   = (const char *)"";
      dimmerContext=mylbcontext->bind_new_context(name);

      initialize_dimmers(dimmerContext);
    }

    /*
      CORBA::String_var sior(orb->object_to_string(lb));
      cout << "IDL object LB::Lightboard IOR = '" << (char*)sior << "'" << endl;
      FILE *f = fopen ("/tmp/lb.ior", "w");
      fputs ((char *)sior, f);
      fputs ("\n", f);
      fclose (f);
    */

    // Obtain a POAManager, and tell the POA to start accepting
    // requests on its objects.
    PortableServer::POAManager_var pman = poa->the_POAManager();
    pman->activate();
    
    initialize_instruments(lb);
    initialize_faders(lb);
    initialize_cuefaders(lb);
    initialize_crossfaders(lb);
    initialize_levelfaders(lb);
 
    load_modules();

    //    CORBA::Object_var obj = rootContext->resolve(name);

    orb->run();
    orb->destroy();
  }
  catch(CORBA::SystemException&) {
    fprintf (stderr, "Caught CORBA::SystemException.\n");
  }
  catch(CORBA::Exception&) {
    fprintf (stderr, "Caught CORBA::Exception.\n");
  }
  catch(omniORB::fatalException& fe) {
    fprintf (stderr, "Caught omniORB::fatalException:\n");
    fprintf (stderr, "  file: %s\n", fe.file());
    fprintf (stderr, "  line: %s\n", fe.line());
    fprintf (stderr, "  mesg: %s\n", fe.errmsg());
  }
  catch(...) {
    fprintf (stderr, "Caught unknown exception.\n");
  }

  return 0;
}
