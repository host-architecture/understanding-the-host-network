#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/debugfs.h>
#include <linux/slab.h>
#include <linux/version.h>
#include <linux/mm.h>
#include <asm/set_memory.h>

 
#define DEV_NAME "miomap"

struct dentry  *file1;
void *miomap_memarea;
int miomap_memarea_numpages;

/* After unmap. */
static void vm_close(struct vm_area_struct *vma)
{
    pr_info("vm_close\n");
}

static vm_fault_t vm_fault(struct vm_fault *vmf)
{
    struct page *page;

    pr_info("vm_fault\n");
    
    page = vmalloc_to_page(miomap_memarea + (vmf->pgoff << PAGE_SHIFT));
    get_page(page);
    vmf->page = page;
    return 0;
}

static void vm_open(struct vm_area_struct *vma)
{
    pr_info("vm_open\n");
}

static struct vm_operations_struct vm_ops =
{
    .close = vm_close,
    .fault = vm_fault,
    .open = vm_open,
};
 
 
int my_mmap(struct file *filp, struct vm_area_struct *vma)
{
    pr_info("miomap mmap called");

    if(miomap_memarea != NULL) {
        pr_info("mmap already called by an active process");
        return -EAGAIN;
    }

    if((vma->vm_end - vma->vm_start) % (1 << PAGE_SHIFT) != 0) {
        pr_info("mmap size not a multiple of page size");
        return -EINVAL;
    }

    miomap_memarea = vmalloc_user(vma->vm_end - vma->vm_start);
    if(miomap_memarea == NULL) {
        pr_info("failed to vmalloc memory");
        return -EAGAIN;
    }

    miomap_memarea_numpages = ((vma->vm_end - vma->vm_start) >> PAGE_SHIFT);

    if(set_memory_wc((unsigned long)miomap_memarea, miomap_memarea_numpages)) {
        pr_info("set_memory_wc failed");
    }

    vma->vm_page_prot = pgprot_writecombine(vma->vm_page_prot);
    vma->vm_ops = &vm_ops;
    pr_info("miomap mmap successful");
    return 0;
}
 
int my_close(struct inode *inode, struct file *filp)
{
    pr_info("miomap close");
    if(miomap_memarea != NULL) {
        if(set_memory_wb((unsigned long)miomap_memarea, miomap_memarea_numpages)) {
            pr_info("set_memory_wb failed");
        }
        vfree(miomap_memarea);
        miomap_memarea = NULL;
        miomap_memarea_numpages = 0;
    }
    return 0;
}
 
int my_open(struct inode *inode, struct file *filp)
{
    pr_info("miomap open");
    pr_info("%d", PAGE_SHIFT);
    return 0;
}
 
static const struct file_operations my_fops = {
    .open = my_open,
    .release = my_close,
    .mmap = my_mmap,
};
 
static int miomap_init(void)
{
    file1 = debugfs_create_file_unsafe(DEV_NAME, 0644, NULL, NULL, &my_fops);
    miomap_memarea = NULL;
    miomap_memarea_numpages = 0;
    return 0;
}
 
static void miomap_exit(void)
{
    debugfs_remove(file1);
 
}
 
module_init(miomap_init);
module_exit(miomap_exit);
MODULE_AUTHOR("Midhul");
MODULE_LICENSE("GPL");