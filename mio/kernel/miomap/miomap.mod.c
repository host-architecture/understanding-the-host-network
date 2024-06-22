#include <linux/build-salt.h>
#include <linux/module.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

BUILD_SALT;

MODULE_INFO(vermagic, VERMAGIC_STRING);
MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(.gnu.linkonce.this_module) = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

#ifdef CONFIG_RETPOLINE
MODULE_INFO(retpoline, "Y");
#endif

static const struct modversion_info ____versions[]
__used __section(__versions) = {
	{ 0xb3753869, "module_layout" },
	{ 0x2600773, "debugfs_remove" },
	{ 0x4348ca90, "debugfs_create_file_unsafe" },
	{ 0x999e8297, "vfree" },
	{ 0x91607d95, "set_memory_wb" },
	{ 0xcc78395e, "vmalloc_to_page" },
	{ 0x50d1f870, "pgprot_writecombine" },
	{ 0x767ddb02, "set_memory_wc" },
	{ 0x5635a60a, "vmalloc_user" },
	{ 0xc5850110, "printk" },
	{ 0xbdfb6dbb, "__fentry__" },
};

MODULE_INFO(depends, "");


MODULE_INFO(srcversion, "C16AD708655336D65B2ED5A");
