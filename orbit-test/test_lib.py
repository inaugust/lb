#!/usr/bin/env python1.5
import CORBA
import sys
import Fruit, Fruit__POA

class Instance(Fruit__POA.Instance):
	def __init__(self, fruit):
		self.fruit = fruit
		self.left = 100

	def bite(self, size):
		if self.left - size < 0:
			exdata = Fruit.Instance.BigBite(too_much_by = size - self.left)
			raise Fruit.Instance.BigBite, exdata
			return

		self.left = self.left - size
		print "Eating %d%%, %d%% left" % (size, self.left)
		self._test_print_foo()
		if self.left == 0:
			raise Fruit.Instance.AllEaten

	def get_factory(self):
		return FFactory()._this()

	def _test_print_foo(self):
		print "I love jookie"

class FFactory(Fruit__POA.FFactory):
	def __init__(self):
		self.fruit_list = []

	def add_fruit(self, f):
		for fruit in self.fruit_list:
			if fruit.name == f.name:
				raise Fruit.FFactory.AlreadyExists
		self.fruit_list.append(f)

	def get_instance(self, fruit):
		return Instance(fruit)._this()

	def discard_instance(self, ref):
		#servant = poa.reference_to_servant(ref)
		#poa.deactivate_object(servant)
		pass

	def get_random_fruit(self):
		import random
		index = random.randint(0, len(self.fruit_list) - 1)
		return index, self.fruit_list[index]

	def test_union(self, color):
		if color == Fruit.orange:
			return Fruit.FFactory.TestUnion(color, "foobar")
		elif color == Fruit.red:
			return Fruit.FFactory.TestUnion(color, 42)
		elif color == Fruit.yellow:
			return Fruit.FFactory.TestUnion(color, 2.71828)
		elif color == Fruit.green:
			return Fruit.FFactory.TestUnion(color, CORBA.TRUE)

	def test_any(self):
		import random
		pick = random.randint(0, 2)
		if pick == 0:
			return CORBA.Any(CORBA.TypeCode("IDL:CORBA/String:1.0"), "abc123")
		elif pick == 1:
			return CORBA.Any(CORBA.TypeCode("IDL:CORBA/Short:1.0"), 42)
		elif pick == 2:
			new_props = Fruit.Properties(name = "pineapple", color = Fruit.yellow)
			return CORBA.Any(CORBA.TypeCode(new_props), new_props)
	def test_list(self, n):
		return range (n)

	def die(self):
		orb.shutdown(CORBA.TRUE)

#orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
#poa = orb.resolve_initial_references("RootPOA")

#def initialize(orb):
#    fruit_fac=FFactory()._this()
    #ref = FFactory()._this() # implicit activation
#    open("./test-server.ior", "w").write(orb.object_to_string(fruit_fac))
#
#poa._get_the_POAManager().activate()
#orb.run()
