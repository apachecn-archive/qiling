#!/usr/bin/env python3
# 
# Cross Platform and Multi Architecture Advanced Binary Emulation Framework
# Built on top of Unicorn emulator (www.unicorn-engine.org) 

from qiling.arch.x86 import *
from qiling.const import *
from qiling.os.const import *
from qiling.os.posix.posix import QlOsPosix
from .const import *

class QlOsFreebsd(QlOsPosix):
    def __init__(self, ql):
        super(QlOsFreebsd, self).__init__(ql)
        self.load()
        
    def load(self):   
        """
        initiate UC needs to be in loader,
        or else it will kill execve
        """
        self.ql.uc = self.ql.arch.init_uc

        if (self.ql.stack_address == 0):
            if self.ql.shellcoder:
                self.ql.stack_address = 0x1000000
            else:
                self.ql.stack_address = QL_X8664_FREEBSD_PREDEFINE_STACKADDRESS
        
        if (self.ql.stack_size == 0):
            if self.ql.shellcoder:
                self.ql.stack_size = 10 * 1024 * 1024
            else:
                self.ql.stack_size = QL_X8664_FREEBSD_PREDEFINE_STACKSIZE
        
        self.ql.mem.map(self.ql.stack_address, self.ql.stack_size)
        
        if self.ql.shellcoder:
            self.ql.stack_address = self.ql.stack_address  + 0x200000 - 0x1000

        init_rbp = self.ql.stack_address + 0x40
        init_rdi = self.ql.stack_address

        self.ql.register(UC_X86_REG_RSP, self.ql.stack_address)
        self.ql.register(UC_X86_REG_RBP, init_rbp)
        self.ql.register(UC_X86_REG_RDI, init_rdi)
        self.ql.register(UC_X86_REG_R14, init_rdi)

        #self.ql.dprint(D_INFO, "[+] RSP = 0x%x" % (self.ql.stack_address))
        #self.ql.dprint(D_INFO, "[+] RBP = 0x%x" % (init_rbp))
        #self.ql.dprint(D_INFO, "[+] RDI = 0x%x" % (init_rdi))

        self.setup_output()
        self.ql.hook_insn(self.hook_syscall, UC_X86_INS_SYSCALL)

        self.gdtm = GDTManager(self.ql)
        ql_x86_register_cs(self)
        ql_x86_register_ds_ss_es(self)
        
    def hook_syscall(self, intno= None):
        return self.load_syscall()


    def run(self):
        if (self.ql.until_addr == 0):
            self.ql.until_addr = self.QL_EMU_END
        try:
            if self.ql.shellcoder:
                self.ql.emu_start(self.ql.stack_address, (self.ql.stack_address + len(self.ql.shellcoder)))
            else:
                if self.ql.loader.elf_entry != self.ql.loader.entry_point:
                    self.ql.emu_start(self.ql.loader.entry_point, self.ql.loader.elf_entry, self.ql.timeout)
                    self.ql.enable_lib_patch()
                self.ql.emu_start(self.ql.loader.elf_entry, self.ql.until_addr, self.ql.timeout)
                
        except UcError:
            if self.ql.output in (QL_OUTPUT.DEBUG, QL_OUTPUT.DUMP, QL_OUTPUT.DISASM):
                self.ql.nprint("[+] PC = 0x%x\n" %(self.ql.reg.pc))
                self.ql.mem.show_mapinfo()
                try:
                    buf = self.ql.mem.read(self.ql.reg.pc, 8)
                    self.ql.nprint("[+] %r" % ([hex(_) for _ in buf]))
                    self.ql.nprint("\n")
                    ql_hook_code_disasm(ql, self.ql.reg.pc, 64)
                except:
                    pass
            raise
        
        if self.ql.internal_exception != None:
            raise self.ql.internal_exception
