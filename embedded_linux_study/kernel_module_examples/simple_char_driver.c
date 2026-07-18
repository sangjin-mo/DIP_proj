// SPDX-License-Identifier: GPL-2.0
#include <linux/fs.h>
#include <linux/init.h>
#include <linux/miscdevice.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/string.h>
#include <linux/uaccess.h>

#define DEVICE_NAME "edu_char"
#define BUFFER_SIZE 128

static char device_buffer[BUFFER_SIZE] = "edu_char is ready\n";
static size_t device_buffer_len = sizeof("edu_char is ready\n") - 1;
static DEFINE_MUTEX(device_buffer_lock);

static ssize_t edu_read(struct file *file, char __user *user_buffer,
			size_t count, loff_t *position)
{
	ssize_t result;

	if (mutex_lock_interruptible(&device_buffer_lock))
		return -ERESTARTSYS;

	result = simple_read_from_buffer(user_buffer, count, position,
					 device_buffer, device_buffer_len);
	mutex_unlock(&device_buffer_lock);

	return result;
}

static ssize_t edu_write(struct file *file, const char __user *user_buffer,
			 size_t count, loff_t *position)
{
	size_t bytes_to_copy;

	if (count == 0)
		return 0;

	bytes_to_copy = min(count, (size_t)BUFFER_SIZE - 1);

	if (mutex_lock_interruptible(&device_buffer_lock))
		return -ERESTARTSYS;

	if (copy_from_user(device_buffer, user_buffer, bytes_to_copy)) {
		mutex_unlock(&device_buffer_lock);
		return -EFAULT;
	}

	device_buffer[bytes_to_copy] = '\0';
	device_buffer_len = bytes_to_copy;
	mutex_unlock(&device_buffer_lock);

	return bytes_to_copy;
}

static const struct file_operations edu_fops = {
	.owner = THIS_MODULE,
	.read = edu_read,
	.write = edu_write,
	.llseek = no_llseek,
};

static struct miscdevice edu_misc_device = {
	.minor = MISC_DYNAMIC_MINOR,
	.name = DEVICE_NAME,
	.fops = &edu_fops,
	.mode = 0600,
};

static int __init edu_driver_init(void)
{
	int result;

	result = misc_register(&edu_misc_device);
	if (result) {
		pr_err("%s: misc_register failed: %d\n", DEVICE_NAME, result);
		return result;
	}

	pr_info("%s: registered /dev/%s\n", DEVICE_NAME, DEVICE_NAME);
	return 0;
}

static void __exit edu_driver_exit(void)
{
	misc_deregister(&edu_misc_device);
	pr_info("%s: unregistered\n", DEVICE_NAME);
}

module_init(edu_driver_init);
module_exit(edu_driver_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Embedded Linux Study");
MODULE_DESCRIPTION("Educational misc character device driver");
MODULE_VERSION("1.0");

