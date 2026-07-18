// SPDX-License-Identifier: GPL-2.0
#include <linux/init.h>
#include <linux/module.h>
#include <linux/moduleparam.h>

static char *message = "hello from the kernel";
module_param(message, charp, 0444);
MODULE_PARM_DESC(message, "Message printed when the module is loaded");

static int __init hello_module_init(void)
{
	pr_info("hello_module: loaded; message=\"%s\"\n", message);
	return 0;
}

static void __exit hello_module_exit(void)
{
	pr_info("hello_module: unloaded\n");
}

module_init(hello_module_init);
module_exit(hello_module_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Embedded Linux Study");
MODULE_DESCRIPTION("Minimal module lifecycle and parameter example");
MODULE_VERSION("1.0");

