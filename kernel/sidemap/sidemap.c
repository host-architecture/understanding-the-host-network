#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/debugfs.h>
#include <linux/slab.h>
#include <linux/version.h>
#include <linux/mm.h>
#include <linux/vmalloc.h>
#include <asm/set_memory.h>

 
#define DEV_NAME_LOCAL "sidemap-local"
#define DEV_NAME_REMOTE "sidemap-remote"

#define LOCAL_NUMA 1
#define REMOTE_NUMA 0
#define FP_SIZE 262144 // 1GiB

struct dentry  *file1;
struct dentry  *file2;
// struct page *one_frame;
// struct vm_area_struct *mapped_vma;
// unsigned long mapped_addr;

// Pool of physical frames to back one mmap'ed region
struct frame_pool {
    struct page **pages;
    struct vm_area_struct **mapped_vmas;
    unsigned long *mapped_addrs;
    int num_pages;
    int nid;
    int page_idx;
};


// Does not free the struct frame_pool itself
static void destroy_frame_pool(struct frame_pool *fp) {
    if(fp == NULL) return;
    int i;
    if(fp->pages != NULL) {
        for(i = 0; i < fp->num_pages; i++) {
            // This works because num_pages is initialized before fp->pages
            if(fp->pages[i] != NULL) {
                ClearPageReserved(fp->pages[i]);
                __free_pages(fp->pages[i], 0);
            }
        }
    }
    kfree(fp->pages);
    kfree(fp->mapped_vmas);
    kfree(fp->mapped_addrs);
    fp->num_pages = 0;
    fp->nid = -1;
    fp->page_idx = 0;
}


static int init_frame_pool(struct frame_pool *fp, int num_pages, int nid) {
    int i;
    // Set num_pages first, so that if page allocation fails midway, destroy_frame_pool can cleanup
    fp->num_pages = num_pages;
    fp->nid = nid;
    fp->page_idx = 0;
    fp->pages = NULL;
    fp->mapped_vmas = NULL;
    fp->mapped_addrs = NULL;
    fp->pages = kcalloc(num_pages, sizeof(struct page *), GFP_KERNEL);
    if(fp->pages == NULL) {
        goto err;
    }
    fp->mapped_vmas = kcalloc(num_pages, sizeof(struct vm_area_struct *), GFP_KERNEL);
    if(fp->mapped_vmas == NULL) {
        goto err;
    }
    fp->mapped_addrs = kcalloc(num_pages, sizeof(unsigned long), GFP_KERNEL);
    if(fp->mapped_addrs == NULL) {
        goto err;
    }
    // Allocate physical frames
    for(i = 0; i < num_pages; i++) {
        fp->pages[i] = alloc_pages_node(nid, GFP_HIGHUSER, 0);
        if(fp->pages[i] == NULL) {
            pr_info("alloc_pages_node failed \n");
            goto err;
        }
        SetPageReserved(fp->pages[i]);
    }

    return 0;

err:

    destroy_frame_pool(fp);
    return -1;
}

static void vm_close(struct vm_area_struct *vma)
{
    pr_info("vm_close\n");
    struct frame_pool *fp = (struct frame_pool *)vma->vm_private_data;
    destroy_frame_pool(fp);
    kfree(fp);
}

static vm_fault_t vm_fault(struct vm_fault *vmf)
{
    vm_fault_t ret;
    struct frame_pool *fp;

    // pr_info("vm_fault\n");

    fp = (struct frame_pool *)vmf->vma->vm_private_data;

    if(fp->mapped_vmas[fp->page_idx] != NULL) {
        // Unmap the page
        zap_vma_ptes(fp->mapped_vmas[fp->page_idx], fp->mapped_addrs[fp->page_idx], PAGE_SIZE);
        // pr_info("Zapped page from previous mapping\n");
        fp->mapped_vmas[fp->page_idx] = NULL;
        fp->mapped_addrs[fp->page_idx] = 0;
    }
    
    ret = vmf_insert_pfn_notrack(vmf->vma, vmf->address, page_to_pfn(fp->pages[fp->page_idx]));
    fp->mapped_vmas[fp->page_idx] = vmf->vma;
    fp->mapped_addrs[fp->page_idx] = vmf->address;

    fp->page_idx = (fp->page_idx + 1) % fp->num_pages;
    // pr_info("vm_insert_pfn done\n");
    return ret;
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
 
 
int __my_mmap(struct file *filp, struct vm_area_struct *vma, int fp_size, int nid)
{
    pr_info("sidemap mmap called");

    // if(one_frame != NULL) {
    //     pr_info("mmap already called by an active process");
    //     return -EAGAIN;
    // }

    if((vma->vm_end - vma->vm_start) % PAGE_SIZE != 0) {
        pr_info("mmap size not a multiple of page size");
        return -EINVAL;
    }

    // one_frame = alloc_pages_node(LOCAL_NUMA, GFP_HIGHUSER, 0);
    // if(one_frame == NULL) {
    //     pr_info("alloc_pages failed");
    //     return -EAGAIN;
    // }
    // SetPageReserved(one_frame);

    // Allocate a frame pool
    struct frame_pool *fp = kzalloc(sizeof(struct frame_pool), GFP_KERNEL);
    if(fp == NULL) {
        pr_info("Failed to allocate frame_pool\n");
        return -EAGAIN;
    }
    if(init_frame_pool(fp, fp_size, nid) != 0) {
        pr_info("Init frame_pool failed\n");
        return -EAGAIN;
    }
    vma->vm_private_data = fp;
    vma->vm_ops = &vm_ops;
    vm_flags_set(vma, VM_PFNMAP | VM_DONTEXPAND | VM_DONTDUMP);
    vma->vm_page_prot = vm_get_page_prot(vma->vm_flags);
    pr_info("sidemap mmap successful");
    return 0;
}

int my_mmap_local(struct file *filp, struct vm_area_struct *vma) {
    return __my_mmap(filp, vma, FP_SIZE, LOCAL_NUMA);
}
 
int my_mmap_remote(struct file *filp, struct vm_area_struct *vma) {
    return __my_mmap(filp, vma, FP_SIZE, REMOTE_NUMA);
}

int my_close(struct inode *inode, struct file *filp)
{
    pr_info("sidemap close");
    // if(one_frame != NULL) {
    //     ClearPageReserved(one_frame);
    //     __free_pages(one_frame, 0);
    //     one_frame = NULL;
    // }
    return 0;
}
 
int my_open(struct inode *inode, struct file *filp)
{
    pr_info("sidemap open");
    pr_info("%ld", PAGE_SIZE);
    return 0;
}
 
static const struct file_operations my_fops_local = {
    .open = my_open,
    .release = my_close,
    .mmap = my_mmap_local,
};

static const struct file_operations my_fops_remote = {
    .open = my_open,
    .release = my_close,
    .mmap = my_mmap_remote,
};
 
static int sidemap_init(void)
{
    file1 = debugfs_create_file_unsafe(DEV_NAME_LOCAL, 0644, NULL, NULL, &my_fops_local);
    file2 = debugfs_create_file_unsafe(DEV_NAME_REMOTE, 0644, NULL, NULL, &my_fops_remote);
    // one_frame = NULL;
    // mapped_vma = NULL;
    // mapped_addr = 0;
    return 0;
}

static void sidemap_exit(void)
{
    debugfs_remove(file1);
    debugfs_remove(file2);
}
 
module_init(sidemap_init);
module_exit(sidemap_exit);
MODULE_AUTHOR("Midhul");
MODULE_LICENSE("GPL");