#include <linux/module.h>
#define INCLUDE_VERMAGIC
#include <linux/build-salt.h>
#include <linux/elfnote-lto.h>
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
	{ 0xe49bb82b, "module_layout" },
	{ 0x49eb08e, "debugfs_remove" },
	{ 0x2e70de82, "debugfs_create_file_unsafe" },
	{ 0x494e3393, "vm_get_page_prot" },
	{ 0xfce190f2, "__alloc_pages" },
	{ 0x60f64c0d, "kmem_cache_alloc_trace" },
	{ 0x3703b5ff, "kmalloc_caches" },
	{ 0xeb233a45, "__kmalloc" },
	{ 0x7bcb1e30, "__free_pages" },
	{ 0x37a0cba, "kfree" },
	{ 0x9524a6a2, "vmf_insert_pfn" },
	{ 0x97651e6c, "vmemmap_base" },
	{ 0xc7d97d5f, "zap_vma_ptes" },
	{ 0x5b8239ca, "__x86_return_thunk" },
	{ 0x92997ed8, "_printk" },
	{ 0xbdfb6dbb, "__fentry__" },
};

MODULE_INFO(depends, "");


MODULE_INFO(srcversion, "9DE757465D7E154411BD4EC");
