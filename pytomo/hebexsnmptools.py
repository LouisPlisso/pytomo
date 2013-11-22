# python-hebexsnmptools module
# Copyright (C) 2013 Pascal Beringuie
# ORANGE/DMGP/Portail/DOP/Hebex 
# The code concerning agentX has been inspired from Bozhin Zafirov
# python-agentX module

import ctypes, ctypes.util
import signal
import sys
import time
import os
import re
import select
import fcntl
from threading import Thread
from threading import Event
from ctypes import sizeof


# export names
__all__ = [
	'ASN_BOOLEAN',
	'ASN_INTEGER',
	'ASN_BIT_STR',
	'ASN_OCTET_STR',
	'ASN_GAUGE',
	'ASN_COUNTER',
	'ASN_COUNTER64',
	'ASN_TIMETICKS',
	'SnmpData',
	'OperationalError',
	'BadOidException',
	'BadValueException',
	'BadTypeException',
	'PassPersist',
	'AgentX',
	'TABLE_INDEX_STRING',
	'TABLE_INDEX_INTEGER',
]

# snmp agentx library
snmp	= None
axl	= None
try:
	snmp	= ctypes.cdll.LoadLibrary(ctypes.util.find_library('netsnmphelpers'))
	axl	= ctypes.cdll.LoadLibrary(ctypes.util.find_library('netsnmpagent'))
except:
	print('ERROR: agentx module requires net-snmp libraries.')
	import sys
	sys.exit(1)

# constants
NETSNMP_DS_APPLICATION_ID	= 1
NETSNMP_DS_AGENT_ROLE		= 1

# ASN constants
ASN_BOOLEAN			= 0x01
ASN_INTEGER			= 0x02
ASN_BIT_STR			= 0x03
ASN_OCTET_STR			= 0x04
ASN_NULL			= 0x05
ASN_OBJECT_ID			= 0x06
ASN_SEQUENCE			= 0x10
ASN_SET				= 0x11
ASN_COUNTER                     = 0x41
ASN_GAUGE			= 0x42
ASN_TIMETICKS			= 0x43
ASN_COUNTER64			= 0x46
ASN_UNIVERSAL			= 0x00
ASN_APPLICATION			= 0x40
ASN_CONTEXT			= 0x80
ASN_PRIVATE			= 0xC0

ASN_PRIMITIVE			= 0x00
ASN_CONSTRUCTOR			= 0x20

ASN_LONG_LEN			= 0x80
ASN_EXTENSION_ID		= 0x1F
ASN_BIT8			= 0x80

ASN_UNSIGNED			= ASN_APPLICATION | 0x2
ASN_TIMETICKS			= ASN_APPLICATION | 0x3
ASN_APP_FLOAT			= ASN_APPLICATION | 0x8
ASN_APP_DOUBLE			= ASN_APPLICATION | 0x9

# asn opaque
ASN_OPAQUE_TAG2			= 0x30
ASN_OPAQUE_FLOAT		= ASN_OPAQUE_TAG2 + ASN_APP_FLOAT
ASN_OPAQUE_DOUBLE		= ASN_OPAQUE_TAG2 + ASN_APP_DOUBLE

# handler constants
HANDLER_CAN_GETANDGETNEXT	= 0x01
HANDLER_CAN_SET			= 0x02
HANDLER_CAN_GETBULK		= 0x04
HANDLER_CAN_NOT_CREATE		= 0x08
HANDLER_CAN_BABY_STEP		= 0x10
HANDLER_CAN_STASH		= 0x20

HANDLER_CAN_RONLY		= HANDLER_CAN_GETANDGETNEXT
HANDLER_CAN_RWRITE		= HANDLER_CAN_GETANDGETNEXT | HANDLER_CAN_SET
HANDLER_CAN_SET_ONLY		= HANDLER_CAN_SET | HANDLER_CAN_NOT_CREATE
HANDLER_CAN_DEFAULT		= HANDLER_CAN_RONLY | HANDLER_CAN_NOT_CREATE

SNMP_ERR_NOERROR		= 0
SNMP_ERR_TOOBIG			= 1
SNMP_ERR_NOSUCHNAME		= 2
SNMP_ERR_BADVALUE		= 3
SNMP_ERR_READONLY		= 4
SNMP_ERR_GENERR			= 5

ASN_CONSTRUCTOR			= 0x20

SNMP_MSG_GET			= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x0
SNMP_MSG_GETNEXT		= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x1
SNMP_MSG_RESPONSE		= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x2
SNMP_MSG_SET			= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x3
SNMP_MSG_TRAP			= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x4
SNMP_MSG_GETBULK		= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x5
SNMP_MSG_INFORM			= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x6
SNMP_MSG_TRAP2			= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x7

SNMP_MSG_INTERNAL_SET_BEGIN	= -1
SNMP_MSG_INTERNAL_SET_RESERVE1	= 0
SNMP_MSG_INTERNAL_SET_RESERVE2	= 1
SNMP_MSG_INTERNAL_SET_ACTION	= 2
SNMP_MSG_INTERNAL_SET_COMMIT	= 3
SNMP_MSG_INTERNAL_SET_FREE	= 4
SNMP_MSG_INTERNAL_SET_UNDO	= 5
SNMP_MSG_INTERNAL_SET_MAX	= 6


MAX_OID_LEN			= 128
OID_LEN				= MAX_OID_LEN*2+1

TABLE_INDEX_INTEGER		= 1
TABLE_INDEX_STRING		= 2


# types 
# oid type definition
oid_t = ctypes.c_ulong
oidOID_t = oid_t * MAX_OID_LEN
strOID_t = ctypes.c_char * OID_LEN


# structures

# dummy structures (pointers only)
class netsnmp_mib_handler(ctypes.Structure): pass
class netsnmp_handler_registration(ctypes.Structure): pass
class netsnmp_subtree(ctypes.Structure): pass
class netsnmp_agent_session(ctypes.Structure): pass
#class counter64(ctypes.Structure): pass

class counter64(ctypes.Structure):
	_fields_ = [
		('hight',             ctypes.c_long),
		('low',             ctypes.c_long),
	]



class netsnmp_vardata(ctypes.Union):
	_fields_ = [
		('integer',		ctypes.POINTER(ctypes.c_long)),
		('string',		ctypes.c_char_p),
		('objid',		ctypes.POINTER(oid_t)),
		('bitstring',		ctypes.POINTER(ctypes.c_ubyte)),
		('counter64',		ctypes.POINTER(counter64)),
		('floatVal',		ctypes.POINTER(ctypes.c_float)),
		('doubleVal',		ctypes.POINTER(ctypes.c_double)),
	]

class netsnmp_variable_list(ctypes.Structure): pass
netsnmp_variable_list._fields_ = [
		('next_variable',	ctypes.POINTER(netsnmp_variable_list)),
		('name',		ctypes.POINTER(oid_t)),
		('name_length',		ctypes.c_size_t),
		('type',		ctypes.c_ubyte),
		('val',			netsnmp_vardata),
		('val_len',		ctypes.c_size_t),
		('name_loc',		oid_t * MAX_OID_LEN),
		('buf',			ctypes.c_ubyte * 40),
		('data',		ctypes.c_void_p),
		('dataFreeHook',	ctypes.c_void_p),
		('index',		ctypes.c_int),
	]
netsnmp_variable_list_p = ctypes.POINTER(netsnmp_variable_list)

class netsnmp_data_list(ctypes.Structure): pass
netsnmp_data_list._fields_ = [
		('next',		ctypes.POINTER(netsnmp_data_list)),
		('name',		ctypes.c_char_p),
		('data',		ctypes.c_void_p),
		('free_func',		ctypes.c_void_p),
	]

class netsnmp_agent_request_info(ctypes.Structure):
	_fields_ = [
		('mode',	ctypes.c_int),
		('asp',		ctypes.POINTER(netsnmp_agent_session)),
		('agent_data',	ctypes.POINTER(netsnmp_data_list)),
	]

class netsnmp_request_info(ctypes.Structure): pass
netsnmp_request_info._fields_ = [
		('requestvb',		ctypes.POINTER(netsnmp_variable_list)),
		('parent_data',		ctypes.POINTER(netsnmp_data_list)),
		('agent_req_info',	ctypes.POINTER(netsnmp_agent_request_info)),
		('range_end',		ctypes.POINTER(oid_t)),
		('range_end_len',	ctypes.c_size_t),
		('delegated',		ctypes.c_int),
		('processed',		ctypes.c_int),
		('inclusive',		ctypes.c_int),
		('status',		ctypes.c_int),
		('index',		ctypes.c_int),
		('repeat',		ctypes.c_int),
		('orig_repeat',		ctypes.c_int),
		('requestvb_start',	ctypes.POINTER(netsnmp_variable_list)),
		('next',		ctypes.POINTER(netsnmp_request_info)),
		('prev',		ctypes.POINTER(netsnmp_request_info)),
		('subtree',		ctypes.POINTER(netsnmp_subtree)),
	]


# various functions argument types
axl.read_objid.argtypes = [ctypes.c_char_p, ctypes.POINTER(oidOID_t), ctypes.POINTER(ctypes.c_size_t)]
axl.snmp_set_var_typed_value.argtypes = [ctypes.POINTER(netsnmp_variable_list), ctypes.c_ubyte, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
axl.snmp_set_var_value.argtypes = [ctypes.POINTER(netsnmp_variable_list), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
axl.snprint_objid.argtypes = [strOID_t, ctypes.c_int, ctypes.POINTER(oid_t), ctypes.c_int]
axl.snmp_varlist_add_variable.argtypes = [ctypes.POINTER(netsnmp_variable_list_p), ctypes.POINTER(oid_t), ctypes.c_long, ctypes.c_ubyte, ctypes.c_char_p, ctypes.c_long]
axl.send_v2trap.argtypes = [netsnmp_variable_list_p]



# exceptions
class OperationalError(Exception): pass
class BadOidException(Exception): pass
class BadTypeException(Exception): pass
class BadValueException(Exception): pass

class Oid:
	"""
        Construction d'un objet OID
        Prend en parametre un oid sous forme de chaine peut commencer par '.' ou directement par un nombre
        """
	def __init__(self, oid_str):
		oid_str = '.' + oid_str
		regex = re.compile("^(\.)?((\.\d+)+)$")
		if(regex.match(oid_str)):
			oid_str = regex.match(oid_str).group(2)
			self.oid_array =  map(int, oid_str[1:].split('.'))
		 	self.print_oid =  oid_str
			self.next_oid = None
			self.is_walkable = True
		else:
			raise BadOidException(oid_str)


	def __gt__(self, oid):
		for i in range(0,min(len(self.oid_array), len(oid.oid_array))):
			if self.oid_array[i] > oid.oid_array[i]:
				return True
			elif self.oid_array[i] < oid.oid_array[i]:
				return False
		#Cas ou un des oid est un suboid d'un autre
		if(len(self.oid_array) > len(oid.oid_array)):
			return True
		else:
			return False

	def __eq__(self,oid):
		return self.print_oid == oid.print_oid
	
	def __str__(self):
		return self.print_oid


	def setNext(self, oid):
		if not(oid > self):
			raise BadOidException("In setNext given oid must succeed current oid")
		self.next_oid = oid
		

	def getNext(self):
		return self.next_oid

	def value_set_for_oid(self):
		return False

	def set_walkable(self, walkable):
		"""When set to false, oid will only appear in get requests and not in getnext requests"""
		self.is_walkable = walkable

class OidValue(Oid):
	"""Object that store a value for an oid"""

	#All types allowed for AgentX are defined here
	#Only types allowed for pass_persist have a string associated
	str_for_type = {
		ASN_BOOLEAN:None,
		ASN_INTEGER:'integer',
		ASN_BIT_STR:None,
		ASN_OCTET_STR:'string',
		ASN_NULL:None,
		ASN_OBJECT_ID:None,
		ASN_SEQUENCE:None,
		ASN_SET:None,
		ASN_COUNTER:'counter',
		ASN_GAUGE:'gauge',
		ASN_TIMETICKS:'timeticks',
		ASN_COUNTER64:'counter64',
	}

	def __init__(self, oidstr, vtype, value):
		Oid.__init__(self, oidstr)
		if not OidValue.str_for_type.has_key(vtype):
			raise BadTypeException('Unknown type {0}'.format(vtype))
		self.vtype = vtype
		if (vtype == ASN_INTEGER or vtype == ASN_COUNTER or vtype == ASN_GAUGE or vtype == ASN_TIMETICKS or vtype ==  ASN_COUNTER64) and type(value) != int:
			raise BadValueException('An integer is expected for value')

		if(vtype == ASN_OCTET_STR and type(value) != str):
			raise BadValueException('A string is expected for value')

		self.value = value


	def update(self, value):
		vtype = self.vtype
		if (vtype == ASN_INTEGER or vtype == ASN_COUNTER or vtype == ASN_GAUGE or vtype == ASN_TIMETICKS or vtype ==  ASN_COUNTER64) and type(value) != int:
                        raise BadValueException('An integer is expected for value')
		if(vtype == ASN_OCTET_STR and type(value) != str):
                        raise BadValueException('A string is expected for value')
		self.value = value
		return self


	def value_set_for_oid(self):
                return True



	def get_str_for_type(self):
		return OidValue.str_for_type[self.vtype]



class OidTable(dict):
	"""
	Class that enables you to manage Oids tables more easily
	"""

	def __init__(self, snmpdata, tableroot, index = TABLE_INDEX_INTEGER, number_of_index = 1):
		"""
		Create a table object
		* snmpdata: the snmpdata in which the table will be inserted
		* table root. The root OID for the table
		* index. indexation type TABLE_INDEX_INTEGER or TABLE_INDEX_STRING
		* number_of_index one for a single indexation, 2 for a double indexation, etc..
		"""
		self.snmpdata = snmpdata
		self.tableroot = tableroot
		self.index = index
		self.number_of_index = number_of_index
		snmpdata.addNode(tableroot)


	def registerValue(self, indexes, vtype, value):
		""" 
		Register a value in table 
		* index. An array of strings if index = TABLE_INDEX_INTEGER, an array of integers if index = TABLE_INDEX_INSTANCE
		* the array must contain as much elements as the value of number_of_index passed in constructor
		* if it's a simple indexation (number_of_index = 1), you can pass only a single instance (integer or string)
		""" 
		def encode_str(str):
			str = '{0}'.format(str)
			ar = [] 
			ar.append('{0}'.format(len(str)))
			for i in range(0,len(str)):
				ar.append('{0}'.format(ord(str[i])))
			return '.'.join(ar)
		if type(indexes) != tuple:
			indexes = (indexes,)
		if len(indexes) != self.number_of_index:
			raise OperationalError('This table as an indexation based on {0} elements (number_of_index) {1}  passed'.format(self.number_of_index, len(indexes)))
		
		oid = self.tableroot
		if self.index == TABLE_INDEX_INTEGER:
			oid +=  '.' + '.'.join(map(str,indexes))
		elif self.index == TABLE_INDEX_STRING:
			oid += '.' + '.'.join(map(encode_str,indexes))
		else:
			raise('Unsupported indexation type {0} '.format(self.index))

		return self.snmpdata.registerVar(oid,vtype, value)



# agentx data object
class SnmpData(dict):

	def __init__(self,root):
		"""
		SnmpData is the structure in which you'll set all your Oids
		*root: root oid (string representation ex: .1.2.3.5.6)
		"""
		dict.__init__(self)
		rootobj = Oid(root)
                self[root] = rootobj
                self.root = rootobj


	def addNode(self,oidstr):
		"""
		Add a node in your structure (an oid that contains no value)
		But you can walk starting from that node
		oidstr: string representation ex: .1.2.3.5.6.1
		"""
		if self.has_key(oidstr):
			return self[oidstr]
		else:
			oidobj = Oid(oidstr)
			self.insertOid(oidobj)
			self[oidobj.__str__()] = oidobj
			return oidobj


	#insert oid in string
	def insertOid(self, oid):
		previous = self.root
		while(not previous.getNext() is None and oid > previous.getNext()):
			previous =  previous.getNext()
		#at the end of this loop we have previous < oid and previous.getNext > oid
                #or previous <oid and previous.getNext = None
		oldnext = previous.getNext()
                previous.setNext(oid)
                if not oldnext is None:
                	oid.setNext(oldnext)


	# register variable
	def registerVar(self, oidstr, vtype, value):
		"""
		Affects a value to oid
		Raises an error if oid has been already registered as a node (with addNode)
		or whith registerVar but with a different type
		If oid is already registered with the same type it will be updated
		It will be inserted if it doen't exist
		*oidstr: tring representation ex: .1.2.3.5.6.1..0
		*vtype: ( ASN_INTEGER,ASN_COUNTER,ASN_GAUGE,ASN_TIMETICKS,ASN_COUNTER64,ASN_OCTET_STR)
		*value: must be an integer for  all vtypes except for ASN_OCTET_STR (a string is required)
		*BEWARE: ASN_COUNTER64 type is not available with PassPersist!!!!!!!!!  
		"""

		if self.has_key(oidstr):
			oid = self[oidstr]
			if not self[oidstr].value_set_for_oid():
				raise OperationalError("Oid {0} is a node so yo can't set a value for it".format(oidstr))
			else:
				if vtype != self[oidstr].vtype:
					raise OperationalError("A registerVar has been already done on this same oid with a different type")
				return oid.update(value)
		else:
			oid =  OidValue(oidstr,vtype,value)
			self.insertOid(oid)
			self[oidstr] = oid
			return oid


	def addTable(self, tableroot, index = TABLE_INDEX_INTEGER, number_of_index = 1):
		"""
		Insert a table in snmpdata
		* table root. The root OID for the table
                * index. indexation type TABLE_INDEX_INTEGER or TABLE_INDEX_STRING
                * number_of_index (1 for a single indexation, 2 for a double indexation, etc..)
		"""
		return OidTable(self, tableroot, index, number_of_index)


	def dump(self):
		"""
		Dump all oids in snmpdata
		"""
		oid = self[self.getRootAsStr()]
                print oid
                while not oid.getNext() is None:
                	oid = oid.getNext()
                        if oid.value_set_for_oid() and oid.is_walkable:
                        	print oid.__str__() + '=' + oid.get_str_for_type() + ':{0}'.format( oid.value)

			
	def getNextValue(self, oidstr):
		#returns OidValue object that succeed oidstr
		#nodes (oid that not contain values) are skipped
		if not self.has_key(oidstr):
			return None
		oid = self[oidstr].getNext()
		while((not oid is None) and (not oid.value_set_for_oid() or not oid.is_walkable)):
			oid = oid.getNext()
		return oid


	def getRootAsStr(self):
		#returns snmp root oid as string
		return self.root.print_oid



class MultipleData:
	"""
	Used only for agentX
	A structure that contains several snmpdata
	Necessary to register an agent X on several snmp roots
	"""

	def __init__(self, snmpdatas):
		if type(snmpdatas) != tuple:
                        snmpdatas = (snmpdatas,)
		self.snmpdatas = snmpdatas


	def get(self, key):
		for snmpdata in self.snmpdatas:
			if snmpdata.has_key( key):
				return snmpdata[key]
		return None

	def has_key(self, key):
                for snmpdata in self.snmpdatas:
                        if snmpdata.has_key( key):
                                return True
                return False

	def getNextValue(self, oid):
		for snmpdata in self.snmpdatas:
			if snmpdata.has_key(oid):
				return snmpdata.getNextValue(oid)
		return None

	def getRoots(self):
		roots = []
		for snmpdata in self.snmpdatas:
			roots.append(snmpdata.getRootAsStr())
		return roots


class PassPersist:

	def __init__(self,snmpdata):
		"""
		Creates a PassPersist object.
		*snmpdata: snmp dataset
		"""
		self.oidreg = re.compile("^((\.\d+)+)$")
		self.snmpdata = snmpdata
		self._stop_event =  Event()
		self.mode = None
		
		
	def Stop(self):
		"""
		Stop PassPersist thread
		"""
		self._stop_event.set()

	def is_running(self):
		"""
		Return True if PassPersist thread is still running
		"""
		return not self._stop_event.isSet()


	def sleep(self, time):
                """
                Can be called in other thread to sleep during time
                sleeping is interrupted when an CtrlC or CtrlD is received
                """
                if self.is_running():
                        self._stop_event.wait(time)


        def Run(self):
		"""
		Start thread that will answer to snmp agent
		You can continue to update your snmpdata object while this thread is running
		"""
		self.thread = Thread(target=self._Run, args=());
		self.thread.daemon = True
		self.thread.start()
	
	def _Run(self):
		#started in PassPersist thread to answer snmp agent
		is_running = True
		try:
			while is_running:
				line = sys.stdin.readline()
				if line == '':
					is_running = False
					break
				else:
					self.new_input(line)
		except Exception as e:
			print e
		finally:	 
			self._stop_event.set()
			return


	def new_input(self, line):
		if line[len(line)-1] == '\n':
			line = line[:-1:]
					
		if line == 'PING':
			print 'PONG'
			sys.stdout.flush()
			self.mode = None
		elif line == 'getnext':
			self.mode = 'getnext'
				
		elif line == 'get':
			self.mode = 'get'
						
		elif self.oidreg.match(line):
			success = False
			if self.snmpdata.has_key(line):
								
				if self.mode == 'get':
					oid = self.snmpdata[line]
					if oid.value_set_for_oid():
						vtype = oid.get_str_for_type()
						if not vtype is None:
							print oid
							print vtype
							print oid.value
							success = True
				elif self.mode == 'getnext':
					if not self.snmpdata.getNextValue(line) is None:
						oid = self.snmpdata.getNextValue(line)
						vtype = oid.get_str_for_type()
						if not vtype is None:
							print oid
							print vtype
							print oid.value
							success = True
			
			if not success:
				print 'NONE'
				sys.stdout.flush()
				self.mode = None
			sys.stdout.flush()
				
		elif line == 'dumpall':
			self.mode = None
			oid = self.snmpdata.dump()
		else:
			print 'NONE'
			self.mode = None


# AgentX object declaration
class AgentX(object):
	"""
	Class to answer snmpagent with agentX
	"""
	snmpdata = None

	# callback function
	HandlerWrapperFunc = ctypes.CFUNCTYPE(
		ctypes.c_int,
		ctypes.POINTER(netsnmp_mib_handler),
		ctypes.POINTER(netsnmp_handler_registration),
		ctypes.POINTER(netsnmp_agent_request_info),
		ctypes.POINTER(netsnmp_request_info)
	)
	# high level handler
	def _handler_wrapper(handler, reginfo, reqinfo, requests):
		r = requests.contents
		snmpdata = AgentX.snmpdata
		#global request_handler
		while True:
			# get object id
			strOID = strOID_t()
			axl.snprint_objid(strOID, OID_LEN, r.requestvb.contents.name, r.requestvb.contents.name_length)
	        	oid = oidOID_t(*(r.requestvb.contents.name)[0:r.requestvb.contents.name_length])
			str_oid = '';
			for i in range(0,r.requestvb.contents.name_length):
				str_oid += '{0}.'.format(ctypes.c_ulong(oid[i]).value)
			# python 3.x stores oid in bytes object
			if type(str_oid) != str:
				str_oid = str_oid.decode()
			str_oid = '.'  + str_oid[:-1]
			reqmode = reqinfo.contents.mode


			def format_value(value,vtype):
		 	# set object type
				size = None	
                		if vtype == ASN_OCTET_STR:
					size = len(value)
                        		value = ctypes.c_char_p(value)
                		elif vtype == ASN_INTEGER or vtype == ASN_GAUGE or vtype == ASN_COUNTER:
                        		value = ctypes.pointer(ctypes.c_int(value))
				elif vtype == ASN_COUNTER64:
					c = counter64()
					c.low = value % (2**32)
					c.hight = int(value / (2**32))
					value = ctypes.pointer(c)
                		elif vtype == ASN_APP_FLOAT:
                        		value = ctypes.pointer(ctypes.c_float(value))
                		else:
                        		raise ValueError('Bad value for vtype not in(ASN_OCTET_STR,ASN_INTEGER,ASN_GAUGE.......)')
                		if not size:
					size = sizeof(ctypes.cast(value, ctypes.POINTER(ctypes.c_ubyte)))
                		return (ctypes.cast(value, ctypes.POINTER(ctypes.c_ubyte)), size)


			if reqmode == SNMP_MSG_GET:
				if snmpdata.has_key(str_oid):
					if snmpdata.get(str_oid).value_set_for_oid():
						(value,vtype) = (snmpdata.get(str_oid).value, snmpdata.get(str_oid).vtype)
						(pvalue,size) = format_value(value,vtype)
						axl.snmp_set_var_typed_value(r.requestvb, vtype, pvalue, size)	
			
			elif reqmode == SNMP_MSG_GETNEXT:
				if snmpdata.has_key(str_oid):
					if snmpdata.getNextValue(str_oid) is None:
						# only set current objid
						oid_list = snmpdata.get(str_oid).oid_array
                				oidOID = (oid_t * len(oid_list)) (*oid_list)
						axl.snmp_set_var_objid(r.requestvb, oidOID,  len(oidOID))

					else:
						# req.SetNext changes req.oid value
						oid = snmpdata.getNextValue(str_oid)
						oid_list = oid.oid_array
						oidOID = (oid_t * len(oid_list)) (*oid_list)
						axl.snmp_set_var_objid(r.requestvb, oidOID,  len(oidOID))
						(value,vtype) = (oid.value, oid.vtype)
						(pvalue,size) = format_value(value,vtype)
						axl.snmp_set_var_typed_value(r.requestvb, vtype, pvalue, size)
			
			elif req.mode == SNMP_MSG_INTERNAL_SET_RESERVE2:
				# Snmpset not implemented
				pass
			if not r.next:
                                break
                        r = r.next.contents
		return SNMP_ERR_NOERROR
	# low level handler
	handler_wrapper = HandlerWrapperFunc(_handler_wrapper)


	def __init__(self, name, data):
		"""
		Creates an agentX. Only one agentX instance can be created in your program
		*name: AgentX name
		*data: snmp dataset
		"""
		self.alarm = 0
		AgentX.snmpdata = MultipleData(data)
		self.name = name
		# save global constants in object's namespace
		for c in globals():
			for prefix in ('ASN_', 'SNMP_', 'HANDLER_', 'PAX_'):
				if c.startswith(prefix):
					setattr(self, c, globals()[c])
					break
		# setup log facility
		axl.snmp_enable_stderrlog()
		axl.netsnmp_ds_set_boolean(NETSNMP_DS_APPLICATION_ID, NETSNMP_DS_AGENT_ROLE, 1)
		# init agent module
		# for win32: winsock_startup()
		axl.init_agent(name)
		axl.init_snmp(name)
		self.agent_registered = False


	def format_value(self,value,vtype):
		#format value to answer the agentX
                otype = None
		if vtype == ASN_OCTET_STR:
                        value = ctypes.c_char_p(value)
                elif vtype == ASN_INTEGER or vtype == ASN_GAUGE or vtype == ASN_COUNTER:
                        value = ctypes.pointer(ctypes.c_int(value))
                elif vtype == ASN_APP_FLOAT:
                        value = ctypes.pointer(ctypes.c_float(value))
                else:
			raise ValueError('Bade value for vtype not in(ASN_OCTET_STR,ASN_INTEGER,ASN_GAUGE.......)')
                size = sizeof(ctypes.cast(value, ctypes.POINTER(ctypes.c_ubyte)))
                return (ctypes.cast(value, ctypes.POINTER(ctypes.c_ubyte)), size)



	def register_agent(self):
		#manages agent registration
		for rootoid in AgentX.snmpdata.getRoots():
			oid_list = AgentX.snmpdata.get(rootoid).oid_array
			root = (oid_t * len(oid_list)) (*oid_list)
                	axl.netsnmp_create_handler_registration.restype = ctypes.POINTER(netsnmp_handler_registration)
                	h = axl.netsnmp_create_handler_registration(
                        	self.name,
                        	AgentX.handler_wrapper,
                        	root, len(oid_list),
                        	HANDLER_CAN_RWRITE,
                        	)
                	if axl.netsnmp_register_handler(h) != 0:
                        	raise OperationalError('SNMP handler registration failure for ' + rootoid)

	
	def Run(self):
		"""
		Start a thread that answers to agentX
		You can continue to update your snmpdata object while this thread is running
		"""
		self.register_agent()
		self.thread = Thread(target=AgentX._Run, args=(self,));
		self.thread.daemon = True
		self.thread.start()

	def _Run(self):
		while True:
			r = axl.agent_check_and_process(True)


