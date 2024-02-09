#include <linux/module.h>
#define INCLUDE_VERMAGIC
#include <linux/build-salt.h>
#include <linux/elfnote-lto.h>
#include <linux/export-internal.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

BUILD_SALT;
BUILD_LTO_INFO;

MODULE_INFO(vermagic, VERMAGIC_STRING);
MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(".gnu.linkonce.this_module") = {
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
__used __section("__versions") = {
	{ 0x4b1e9367, "zap_vma_ptes" },
	{ 0x97651e6c, "vmemmap_base" },
	{ 0x770f0976, "vmf_insert_pfn_notrack" },
	{ 0x84bdf0e4, "__free_pages" },
	{ 0x37a0cba, "kfree" },
	{ 0xfa390dd7, "debugfs_create_file_unsafe" },
	{ 0xf1c5625d, "debugfs_remove" },
	{ 0x84ce2451, "kmalloc_caches" },
	{ 0x26e5cd14, "kmalloc_trace" },
	{ 0xeb233a45, "__kmalloc" },
	{ 0x618911fc, "numa_node" },
	{ 0x494bac49, "__alloc_pages" },
	{ 0x494e3393, "vm_get_page_prot" },
	{ 0xbdfb6dbb, "__fentry__" },
	{ 0x122c3a7e, "_printk" },
	{ 0x5b8239ca, "__x86_return_thunk" },
	{ 0x1246a127, "module_layout" },
};

MODULE_INFO(depends, "");


MODULE_INFO(srcversion, "D0C71FF93FD3D4347D57046");
